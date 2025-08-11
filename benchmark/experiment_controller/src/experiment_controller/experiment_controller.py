import re
from threading import Timer

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
        inject_delay = parse_time_to_seconds(self.config.anomaly_injection_period)

        if self.config.elastic_controller_config:
            self.elastic_controller.activate_all()

        # Schedule anomaly injection using a timer
        Timer(
            inject_delay,
            self.inject_anomaly,
        ).start()

        self.workload_generator.start()

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
        Timer(anomaly_duration, self.clean_anomaly)

    def clean_anomaly(self):
        """Cleans up the injected anomaly.

        This method calls the fault injector's clean method to remove the fault.
        """
        self.fault_controller.clean()
        if self.config.elastic_controller_config:
            self.elastic_controller.deactivate_all()
        logger.info(
            f"🛠️  Anomaly finished: {self.config.fault_config.fault_type} "
            f"after {self.config.fault_config.duration} in experiment: {self.config.experiment_name}"
        )
