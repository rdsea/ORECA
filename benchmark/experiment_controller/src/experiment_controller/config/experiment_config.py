from pathlib import Path

import yaml
from experiment_controller.config.anomaly_model import (
    FaultConfig,
)
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
    observability_cleanup_script: str | None = None
    application_cleanup_script: str | None = None


class RCAExperimentConfig(BaseModel):
    """Configuration for an RCA experiment."""

    experiment_name: str
    number_of_run: int
    time_between_run: str
    warm_up_interval: str
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


# Custom representer for Path objects
def path_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.add_representer(Path, path_representer)


def rca_experiment_config_to_yaml(config: RCAExperimentConfig, path: Path):
    """Converts an RCAExperimentConfig to a YAML file."""
    with open(path, "w") as f:
        yaml.dump(config.model_dump(), f, indent=4)
