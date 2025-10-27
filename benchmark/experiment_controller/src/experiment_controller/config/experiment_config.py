from pathlib import Path

import yaml
from experiment_controller.config.anomaly_model import (
    FaultConfig,
)
from experiment_controller.config.workload_config import WorkloadConfig
from experiment_controller.elastic_controller.elastic_controller import (
    ElasticConfig,
)
from experiment_controller.observability_controller.log_controller import (
    LogControllerConfig,
)
from experiment_controller.observability_controller.metric_controller import (
    MetricControllerConfig,
)
from experiment_controller.observability_controller.trace_controller import (
    TraceControllerConfig,
)
from pydantic import BaseModel


class DataCollectorConfig(BaseModel):
    metric_url: str
    trace_url: str | None = None


class CleanUpConfig(BaseModel):
    activate: bool
    observability_cleanup_script: str | None = None
    application_cleanup_script: str | None = None


class ObservabilityCadenceConfig(BaseModel):
    metric_config: MetricControllerConfig | None = None
    trace_config: TraceControllerConfig | None = None
    log_config: LogControllerConfig | None = None


class RootCauseConfig(BaseModel):
    what: str | None = None
    where: str | None = None
    when: str | None = None


class RCAExperimentConfig(BaseModel):
    """Configuration for an RCA experiment."""

    experiment_name: str
    number_of_run: int
    time_between_run: str
    warm_up_interval: str
    clean_up: CleanUpConfig
    fault_config: FaultConfig
    root_cause: RootCauseConfig
    # When to inject the anomaly, for example, 5, 10 minutes after starting load generation
    workload: WorkloadConfig
    elastic_config: ElasticConfig | None = None
    observability_cadence_config: ObservabilityCadenceConfig | None = None
    data_collector_config: DataCollectorConfig


# Custom representer for Path objects
def path_representer(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data))


yaml.add_representer(Path, path_representer)


def rca_experiment_config_to_yaml(config: RCAExperimentConfig, path: Path):
    """Converts an RCAExperimentConfig to a YAML file."""
    with open(path, "w") as f:
        yaml.dump(config.model_dump(), f, indent=4)
