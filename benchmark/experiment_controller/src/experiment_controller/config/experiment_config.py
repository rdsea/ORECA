from pathlib import Path

from experiment_controller.config.anomaly_model import FaultConfig
from experiment_controller.config.workload_config import WorkloadConfig
from experiment_controller.elastic_controller.elastic_controller import (
    ElasticControllerConfig,
)
from pydantic import BaseModel


class MonitorConfig(BaseModel):
    metric_url: str
    namespace: str
    kubernetes_path: str


class CleanUpConfig(BaseModel):
    activate: bool
    observability_cleanup_script: Path | None
    application_cleanup_script: Path | None


class RCAExperimentConfig(BaseModel):
    """Configuration for an RCA experiment."""

    experiment_name: str
    number_of_run: int
    time_between_run: str
    clean_up: CleanUpConfig
    fault_config: FaultConfig
    ground_truth: str
    # When to inject the anomaly, for example, 5, 10 minutes after starting load generation
    anomaly_injection_period: str
    list_of_generator: list[str]
    ssh_username: str
    workload: WorkloadConfig
    elastic_controller_config: ElasticControllerConfig | None = None
    monitor_config: MonitorConfig
