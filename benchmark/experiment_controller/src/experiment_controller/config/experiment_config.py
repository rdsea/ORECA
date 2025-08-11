from experiment_controller.config.anomaly_model import FaultConfig
from experiment_controller.config.workload_config import WorkloadConfig
from experiment_controller.elastic_controller.elastic_controller import (
    ElasticControllerConfig,
)
from pydantic import BaseModel


class RCAExperimentConfig(BaseModel):
    """Configuration for an RCA experiment."""

    experiment_name: str
    fault_config: FaultConfig
    # When to inject the anomaly, for example, 5, 10 minutes after starting load generation
    anomaly_injection_period: str
    list_of_generator: list[str]
    ssh_username: str
    workload: WorkloadConfig
    elastic_controller_config: ElasticControllerConfig | None = None
