from experiment.config.fault_config import FaultSpecificConfig, TargetSelector
from pydantic import BaseModel, model_validator


class StressCPUConfig(BaseModel):
    """
    Configuration for CPU stress.

    Attributes:
        workers (int): Number of CPU workers to use.
        load (int | None): CPU load percentage (0-100). Optional.
    """

    workers: int
    load: int | None = None


class StressMemoryConfig(BaseModel):
    """
    Configuration for memory stress.

    Attributes:
        workers (int): Number of memory workers.
        size (str): Amount of memory to allocate per worker (e.g., "500Mi").
    """

    workers: int
    size: str


class StressChaosConfig(FaultSpecificConfig):
    """
    Configuration for StressChaos.

    Attributes:
        name (str): Experiment name.
        namespace (str): Kubernetes namespace.
        target (TargetSelector): Target pods to stress.
        duration (str): Duration of the stress.
        stress_cpu (StressCPUConfig | None): CPU stress config.
        stress_memory (StressMemoryConfig | None): Memory stress config.
    """

    name: str
    namespace: str = "default"
    target: TargetSelector
    duration: str
    stress_cpu: StressCPUConfig | None = None
    stress_memory: StressMemoryConfig | None = None

    @model_validator(mode="before")
    def validate_at_least_one_stress(cls, values):
        if not any(values.get(key) for key in ["stress_cpu", "stress_memory"]):
            raise ValueError(
                "At least one of 'stress_cpu' or 'stress_memory' must be specified."
            )
        return values
