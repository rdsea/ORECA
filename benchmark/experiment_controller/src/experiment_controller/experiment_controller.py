import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from threading import Timer

from rca_methods.observer.metric_api import ALL_METRICS, PrometheusAPI, monitor_config

from experiment_controller.config.experiment_config import RCAExperimentConfig
from experiment_controller.config.workload_config import (
    DockerWorkloadConfig,
    ShellWorkloadConfig,
)
from experiment_controller.elastic_controller.elastic_controller import (
    ElasticController,
)
from experiment_controller.fault_controller.base import FaultController
from experiment_controller.logger import logger
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

    def __init__(self, config: RCAExperimentConfig):
        """Initialize the RCAExperiment.

        Args:
            config (RCAExperimentConfig): The configuration for the experiment.
        """
        self.config = config
        self.fault_controller = FaultController(self.config.fault_config)
        self.workload_generator = self._create_workload_generator()
        if self.config.elastic_controller_config:
            self.elastic_controller = ElasticController(
                self.config.elastic_controller_config
            )

    def _create_workload_generator(self) -> WorkloadController:
        workload_config = self.config.workload
        if isinstance(workload_config.config, DockerWorkloadConfig):
            return DockerWorkloadGenerator(
                hosts=self.config.list_of_generator,
                ssh_username=self.config.ssh_username,
                docker_image=workload_config.config.image,
                docker_args=workload_config.config.args,
            )
        elif isinstance(workload_config.config, ShellWorkloadConfig):
            return ShellWorkloadGenerator(
                hosts=self.config.list_of_generator,
                ssh_username=self.config.ssh_username,
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

        current_path = Path(__file__).parent
        for i in range(self.config.number_of_run):
            inject_delay = parse_time_to_seconds(self.config.anomaly_injection_period)
            save_path = current_path / self.config.experiment_name / str(i + 1)

            if self.config.elastic_controller_config:
                self.elastic_controller.activate_all()

            # Schedule anomaly injection using a timer
            Timer(
                inject_delay,
                self.inject_anomaly,
            ).start()

            self.workload_generator.start()
            if self.config.clean_up:
                self.clean_up_after_experiment()
            if self.config.number_of_run > 1:
                time.sleep(parse_time_to_seconds(self.config.time_between_run))

            self.collect_telemetry(save_path)

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
        if self.config.elastic_controller_config:
            self.elastic_controller.deactivate_all()
        logger.info(
            f"🛠️  Anomaly finished: {self.config.fault_config.fault_type} "
            f"after {self.config.fault_config.duration} in experiment: {self.config.experiment_name}"
        )

    def clean_up_after_experiment(self):
        pass

    def collect_telemetry(self, save_path: Path):
        self.collect_metric(save_path)
        self.collect_log()
        self.collect_trace()

    def collect_metric(self, save_path: Path):
        prom = PrometheusAPI(self.config.monitor_config.metric_url)

        # Define time range for exporting metrics
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=17)
        # injection_time = 1753213321

        logger.info(f"Start querying metrics from {monitor_config['prometheus_url']}")
        prom.query_range(
            ALL_METRICS,
            start_time,
            end_time,
            save_path=save_path,
            experiment_name=self.config.experiment_name,
            step="1s",
        )
        logger.info("Finished querying metrics")

    def collect_log(self):
        pass

    def collect_trace(self):
        pass
