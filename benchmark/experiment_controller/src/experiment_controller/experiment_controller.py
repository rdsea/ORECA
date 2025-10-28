import os
import re
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from threading import Timer

import yaml

from experiment_controller.config.experiment_config import RCAExperimentConfig
from experiment_controller.config.workload_config import (
    DockerWorkloadConfig,
    ShellWorkloadConfig,
)
from experiment_controller.data_collector.metric_collector import (
    RAW_METRICS,
    SERVICE_METRICS,
    MetricCollector,
)
from experiment_controller.data_collector.trace_collector import TraceCollector
from experiment_controller.elastic_controller.elastic_controller import (
    ElasticController,
)
from experiment_controller.fault_controller.base import FaultController
from experiment_controller.logger import logger
from experiment_controller.observability_controller.log_controller import LogController
from experiment_controller.observability_controller.metric_controller import (
    MetricController,
)
from experiment_controller.observability_controller.trace_controller import (
    TraceController,
)
from experiment_controller.script_runner import ScriptRunner
from experiment_controller.workload_controller.base import WorkloadController
from experiment_controller.workload_controller.docker import DockerWorkloadGenerator
from experiment_controller.workload_controller.shell import ShellWorkloadGenerator


def parse_time_to_seconds(time_str: str) -> int:
    """
    Converts a duration string like '5m', '10s', or '1h' into seconds.

    Args:
        time_str (str): Duration string.

    Returns:
        int: Duration in seconds.

    Raises:
        ValueError: If format is unrecognized.
    """
    match = re.match(r"(\d+)([smh])", time_str.lower())
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")

    value, unit = int(match[1]), match[2]
    return {"s": value, "m": value * 60, "h": value * 3600}[unit]


class RCAExperiment:
    """Runs an end-to-end root cause analysis experiment.

    This class generates traffic and injects network anomalies (e.g., delay, loss, etc.)
    on remote nodes over SSH.

    Attributes:
        config (RCAExperimentConfig): Validated configuration model.
    """

    def __init__(self, config: RCAExperimentConfig, output_dir: Path):
        """Initialize the RCAExperiment.

        Args:
            config (RCAExperimentConfig): The configuration for the experiment.
            output_dir (Path | None): The output directory for the experiment.
        """
        self.config = config
        self.output_dir = output_dir / self.config.experiment_name
        self.fault_controller = FaultController(self.config.fault_config)
        self.workload_generator = self._create_workload_generator()
        self.script_runner = ScriptRunner()
        os.makedirs(self.output_dir, exist_ok=True)
        with open(
            self.output_dir / "experiment_config.yaml",
            "w",
        ) as f:
            logger.debug(self.config.model_dump())
            yaml.dump(self.config.model_dump(exclude_none=True), f)
        if self.config.elastic_config:
            self.elastic_controller = ElasticController(self.config.elastic_config)

    def _create_workload_generator(self) -> WorkloadController:
        workload_config = self.config.workload
        if isinstance(workload_config.config, DockerWorkloadConfig):
            return DockerWorkloadGenerator(
                hosts=workload_config.list_of_generator,
                ssh_username=workload_config.ssh_username,
                docker_image=workload_config.config.image,
                docker_args=workload_config.config.args,
            )
        elif isinstance(workload_config.config, ShellWorkloadConfig):
            return ShellWorkloadGenerator(
                hosts=workload_config.list_of_generator,
                ssh_username=workload_config.ssh_username,
                script_path=workload_config.config.script_path,
                script_args=workload_config.config.script_args,
            )
        else:
            raise ValueError(f"Invalid workload type: {workload_config.type}")

    def run(self):
        """Starts the RCA experiment.

        This method distributes load generator jobs across remote machines and
        schedules delayed fault injection.
        """

        for i in range(self.config.number_of_run):
            inject_delay = parse_time_to_seconds(
                self.config.fault_config.fault_injection_period
            )
            save_path = self.output_dir / str(i + 1)
            os.makedirs(save_path, exist_ok=True)

            try:
                if self.config.clean_up.activate:
                    self.clean_up_after_experiment()

                # Apply elastic  config
                if self.config.elastic_config:
                    self.elastic_controller.activate_all()

                # Apply observability cadence config
                if self.config.observability_cadence_config:
                    if self.config.observability_cadence_config.metric_config:
                        self.metric_controller = MetricController(
                            self.config.observability_cadence_config.metric_config
                        )
                        self.metric_controller.apply()
                    if self.config.observability_cadence_config.trace_config:
                        self.trace_controller = TraceController(
                            self.config.observability_cadence_config.trace_config
                        )
                        self.trace_controller.apply()
                    if self.config.observability_cadence_config.log_config:
                        self.log_controller = LogController(
                            self.config.observability_cadence_config.log_config
                        )
                        self.log_controller.apply()

                # Schedule anomaly injection using a timer
                Timer(
                    inject_delay,
                    self.inject_anomaly,
                ).start()

                start_time = datetime.now()
                self.workload_generator.start()
                end_time = datetime.now()
                warm_up_interval_in_sec = parse_time_to_seconds(
                    self.config.warm_up_interval
                )
                self.collect_telemetry(
                    save_path,
                    start_time + timedelta(seconds=warm_up_interval_in_sec),
                    end_time,
                )
                if self.config.number_of_run > 1:
                    time.sleep(parse_time_to_seconds(self.config.time_between_run))
            except Exception as e:
                logger.exception(f"Experiment failed: {e}")
                with open(save_path / "status.txt", "w") as f:
                    traceback.print_exc(file=f)

    def inject_anomaly(self):
        """Injects the configured anomaly.

        This method applies the fault using the fault injector and schedules
        its cleanup after the specified duration.
        """
        anomaly_duration = parse_time_to_seconds(self.config.fault_config.duration)
        logger.info(
            f"🔧 Injecting anomaly: {self.config.fault_config.fault_type} "
            f"for {self.config.fault_config.duration} in experiment: {self.config.experiment_name}"
        )

        self.fault_controller.inject()
        Timer(anomaly_duration, self.clean_anomaly).start()

    def clean_anomaly(self):
        """Cleans up the injected anomaly.

        This method calls the fault injector's clean method to remove the fault.
        """
        logger.info("Cleaning up the anomaly")
        self.fault_controller.clean()
        if self.config.elastic_config:
            self.elastic_controller.deactivate_all()
        logger.info(
            f"🛠️  Anomaly finished: {self.config.fault_config.fault_type} "
            f"after {self.config.fault_config.duration} in experiment: {self.config.experiment_name}"
        )

    def clean_up_after_experiment(self):
        if (
            self.config.clean_up.observability_cleanup_script is None
            and self.config.clean_up.application_cleanup_script is None
        ):
            logger.error(
                "Observability or application clean up script need to be provided"
            )
            raise ValueError(
                "As clean up is activated, either observability or application script path need to be provided"
            )
        if self.config.clean_up.application_cleanup_script:
            logger.info("Cleaning up application")
            self.script_runner.run_retry(
                self.config.clean_up.application_cleanup_script
            )
        if self.config.clean_up.observability_cleanup_script:
            logger.info("Cleaning up observability")
            self.script_runner.run_retry(
                self.config.clean_up.observability_cleanup_script
            )
        logger.info("Clean up completed")

    def collect_telemetry(
        self,
        save_path: Path,
        experiment_startime: datetime,
        experiment_endtime: datetime,
    ):
        self.collect_metric(save_path, experiment_startime, experiment_endtime)
        self.collect_log()
        self.collect_trace(save_path, experiment_startime, experiment_endtime)

    def collect_metric(
        self,
        save_path: Path,
        experiment_startime: datetime,
        experiment_endtime: datetime,
    ):
        prom = MetricCollector(self.config.data_collector_config.metric_url)

        logger.info(
            f"Start querying metrics from {self.config.data_collector_config.metric_url}"
        )

        # Query and save SERVICE_METRICS
        prom.query_range(
            SERVICE_METRICS,
            experiment_startime,
            experiment_endtime,
            save_path=save_path,
            step="1s",
        )

        # Query and save RAW_METRICS to a separate file
        prom.query_range(
            RAW_METRICS,
            experiment_startime,
            experiment_endtime,
            save_path=save_path,
            step="1s",
            metric_type="raw",  # Specify raw metric type to save to separate file
        )

        logger.info("Finished querying metrics")

    def collect_log(self):
        pass

    def collect_trace(
        self,
        save_path: Path,
        experiment_startime: datetime,
        experiment_endtime: datetime,
    ):
        if (
            self.config.data_collector_config
            and self.config.data_collector_config.trace_url
        ):
            tempo = TraceCollector(self.config.data_collector_config.trace_url)

            logger.info(
                f"Start querying traces from {self.config.data_collector_config.trace_url}"
            )

            # Collect traces for the experiment duration
            tempo.query_range(
                experiment_startime,
                experiment_endtime,
                save_path=save_path,
                experiment_name=self.config.experiment_name,
                limit=1000,  # Collect up to 1000 traces
            )
            logger.info("Finished querying traces")
        else:
            logger.warning("Trace URL not configured, skipping trace collection")
