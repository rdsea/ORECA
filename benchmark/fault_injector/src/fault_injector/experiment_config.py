import logging
import re
import select
import time
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from threading import Timer
from typing import NamedTuple

import paramiko
import yaml
from pydantic import BaseModel, field_validator


class AnomalyCategory(Enum):
    APPLICATION = "Application anomaly"
    WORKLOAD = "Workload anomaly"
    PLATFORM = "Platform anomaly"
    SYSTEM = "System anomaly"


class AnomalyInfo(NamedTuple):
    label: str
    category: AnomalyCategory


class AnomalyEnum(Enum):
    @property
    def label(self) -> str:
        return self.value.label

    @property
    def category(self) -> AnomalyCategory:
        return self.value.category


class ResourceHog(AnomalyEnum):
    CPU = AnomalyInfo("Cpu", AnomalyCategory.PLATFORM)
    MEMORY = AnomalyInfo("Memory", AnomalyCategory.PLATFORM)
    IO = AnomalyInfo("Io", AnomalyCategory.PLATFORM)
    SOCKET = AnomalyInfo("Socket", AnomalyCategory.PLATFORM)


class NetworkFault(Enum):
    DELAY = AnomalyInfo("Delay", AnomalyCategory.SYSTEM)
    DROP = AnomalyInfo("Package drop", AnomalyCategory.SYSTEM)


class CodeLevelFault(AnomalyEnum):
    INCORECT_PARAMETER_VALUE = AnomalyInfo(
        "Incorrect parameter values", AnomalyCategory.APPLICATION
    )
    MISSING_PARAMETER = AnomalyInfo("Missing parameter", AnomalyCategory.APPLICATION)
    MISSING_FUNCTION_CALL = AnomalyInfo(
        "Missing function call", AnomalyCategory.APPLICATION
    )
    INCORRECT_RETURN_VALUE = AnomalyInfo(
        "Incorrect return value", AnomalyCategory.APPLICATION
    )
    MISSING_EXCEPTION_HANDLER = AnomalyInfo(
        "Missing exception handler", AnomalyCategory.APPLICATION
    )


ALL_ANOMALY_ENUMS = {
    f"{cls.__name__}.{e.name}": e
    for cls in [ResourceHog, NetworkFault, CodeLevelFault]
    for e in cls
}


def parse_time_to_seconds(time_str: str) -> int:
    """Parses strings like '5m', '10s', '1h' into seconds."""
    match = re.match(r"(\d+)([smh])", time_str.lower())
    if not match:
        raise ValueError(f"Invalid time format: {time_str}")

    value, unit = int(match[1]), match[2]
    if unit == "s":
        return value
    elif unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    else:
        raise ValueError(f"Unknown time unit in: {time_str}")


class FaultConfig(BaseModel):
    duration: str
    fault_type: AnomalyEnum

    @field_validator("fault_type", mode="before")
    @classmethod
    def parse_fault_type(cls, v):
        if isinstance(v, AnomalyEnum):
            return v
        try:
            return ALL_ANOMALY_ENUMS[v]
        except KeyError:
            raise ValueError(f"Unknown fault_type: {v}")


class RCAExperimentConfig(BaseModel):
    experiment_name: str
    fault_config: FaultConfig
    # When to inject the anomaly, for example, 5, 10 minutes after starting load generation
    anomaly_injection_period: str
    normal_rqs: int
    # Ip for ssh
    load_generate_duration: str
    list_of_generator: list[str]
    spawn_rate: float
    ssh_username: str
    gateway_ip: str


class RCAExperiment:
    def __init__(self, config: RCAExperimentConfig):
        self.config = config

    def _ssh_run_command(self, host: str, command: str) -> str:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=self.config.ssh_username)

            transport = ssh.get_transport()
            channel = transport.open_session()
            channel.get_pty()  # Allocate a pseudo-terminal
            channel.exec_command(command)

            print(f"--- [{host}] Output ---")
            while True:
                # Wait for data to be available
                rl, wl, xl = select.select([channel], [], [], 1.0)
                if channel in rl:
                    try:
                        output = channel.recv(1024).decode("utf-8")
                        if output:
                            print(output, end="", flush=True)
                    except Exception as e:
                        print(f"Error reading from channel: {e}")

                if channel.exit_status_ready():
                    break

            exit_status = channel.recv_exit_status()
            ssh.close()

            return f"\n--- [{host}] Command finished with exit code {exit_status} ---"
        except Exception as e:
            return f"Host: {host}\nError: {e}"

    def run(self):
        individual_genrator_rqs = int(
            self.config.normal_rqs / len(self.config.list_of_generator)
        )
        # Set the timer for injecting the fault
        inject_delay = parse_time_to_seconds(self.config.anomaly_injection_period)
        Timer(
            inject_delay, self.inject_anomaly, args=(self.config.fault_config.duration,)
        ).start()

        # Start the load generation
        command_to_run = f"""docker run --network host  rdsea/object_detection_client:latest \
                            --host http://{self.config.gateway_ip} \
                            --user {individual_genrator_rqs} \
                            --run-time {self.config.load_generate_duration} \
                            --spawn-rate {self.config.spawn_rate}"""
        logging.info(command_to_run)

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._ssh_run_command, host, command_to_run)
                for host in self.config.list_of_generator
            ]

            for future in futures:
                print(future.result())

    def inject_anomaly(self, duration: str):
        anomaly_duration = parse_time_to_seconds(duration)
        logging.info(
            f"Injecting anomaly of type {self.config.fault_config.fault_type} for {duration} into experiment {self.config.experiment_name}"
        )
        time.sleep(anomaly_duration)
        logging.info(
            f"Finished injecting anomaly of type {self.config.fault_config.fault_type} for {duration} into experiment {self.config.experiment_name}"
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s - %(message)s",
    )
    experiment_config = RCAExperimentConfig(
        **yaml.safe_load(open("experiment_config.yaml"))
    )
    experiment = RCAExperiment(experiment_config)

    experiment.run()
