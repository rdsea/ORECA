import logging
import os
import pathlib
import re
import select
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from threading import Timer

import paramiko
import yaml
from rca_methods.observer import (
    monitor_config,
)
from rca_methods.observer.metric_api import ALL_METRICS, PrometheusAPI

from experiment.config.anomaly_model import RCAExperimentConfig
from experiment.fault_injector.base import FaultInjector


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
        self.fault_injector = FaultInjector(self.config.fault_config)

    def _ssh_run_command(self, host: str, command: str) -> str:
        """Run a command on a remote machine via SSH and stream output.

        Args:
            host (str): Remote hostname or IP.
            command (str): Shell command to execute.

        Returns:
            str: Exit status message or error.
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=self.config.ssh_username)

            transport = ssh.get_transport()
            channel = transport.open_session()
            channel.get_pty()
            channel.exec_command(command)

            logging.info(f"--- [{host}] Command started ---")
            while True:
                rl, _, _ = select.select([channel], [], [], 1.0)
                if channel in rl:
                    try:
                        output = channel.recv(1024).decode("utf-8")
                        if output:
                            print(output, end="", flush=True)
                    except Exception as e:
                        logging.error(f"[{host}] Error reading output: {e}")

                if channel.exit_status_ready():
                    break

            exit_status = channel.recv_exit_status()
            ssh.close()

            return f"--- [{host}] Command finished with exit code {exit_status} ---"
        except Exception as e:
            return f"--- [{host}] SSH command failed ---\nError: {e}"

    def run(self):
        """Starts the RCA experiment.

        This method distributes load generator jobs across remote machines and
        schedules delayed fault injection.
        """
        num_generators = len(self.config.list_of_generator)
        if num_generators == 0:
            raise ValueError("No load generator hosts provided.")

        rqs_per_generator = int(self.config.normal_rqs / num_generators)
        inject_delay = parse_time_to_seconds(self.config.anomaly_injection_period)

        # Schedule anomaly injection using a timer
        Timer(
            inject_delay,
            self.inject_anomaly,
        ).start()

        command_to_run = f"""docker run --network host rdsea/object_detection_client:latest \
            --host http://{self.config.gateway_ip} \
            --user {rqs_per_generator} \
            --run-time {self.config.load_generate_duration} \
            --spawn-rate {self.config.spawn_rate}"""

        logging.info("Starting load generators on remote nodes...")
        logging.debug(f"Command: {command_to_run}")

        with ThreadPoolExecutor(max_workers=num_generators) as executor:
            futures = [
                executor.submit(self._ssh_run_command, host, command_to_run)
                for host in self.config.list_of_generator
            ]

            for future in futures:
                result = future.result()
                print(result)

    def inject_anomaly(self):
        """Injects the configured anomaly.

        This method applies the fault using the fault injector and schedules
        its cleanup after the specified duration.
        """
        anomaly_duration = parse_time_to_seconds(self.config.fault_config.duration)
        logging.info(
            f"🔧 Injecting anomaly: {self.config.fault_config.fault_type} "
            f"for {self.config.fault_config.duration} in experiment: {self.config.experiment_name}"
        )

        self.fault_injector.inject()
        Timer(anomaly_duration, self.clean_anomaly)

    def clean_anomaly(self):
        """Cleans up the injected anomaly.

        This method calls the fault injector's clean method to remove the fault.
        """
        self.fault_injector.clean()
        logging.info(
            f"🛠️  Anomaly finished: {self.config.fault_config.fault_type} "
            f"after {self.config.fault_config.duration} in experiment: {self.config.experiment_name}"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s - %(message)s",
    )
    try:
        current_path = pathlib.Path(__file__).parent
        config_path = current_path / "config" / "examples"
        for file in os.listdir(config_path):
            if "network" not in file:
                continue
            with open(config_path / file) as f:
                config_data = yaml.safe_load(f)

            for i in range(1, 4):
                experiment_config = RCAExperimentConfig(**config_data)
                experiment = RCAExperiment(experiment_config)

                # Uncomment to run
                experiment.run()

                prom = PrometheusAPI(monitor_config["prometheus_url"])

                # Define time range for exporting metrics
                end_time = datetime.now()
                start_time = end_time - timedelta(minutes=17)
                # injection_time = 1753213321

                prom.query_range(
                    ALL_METRICS,
                    start_time,
                    end_time,
                    experiment_name=f"{file.split('.')[0]}_{i}",
                    step="1s",
                )
    except Exception as e:
        logging.error(f"Failed to start experiment: {e}")
