from experiment_controller.config.fault_config import (
    FaultSpecificConfig,
    TargetSelector,
)
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


class IOChaosConfig(BaseModel):
    action: str
    path: str
    percent: str
    delay: str | None = None
    errno: int | None = None
    methods: list[str] | None = None


class ResourcesChaosConfig(FaultSpecificConfig):
    """
    General Chaos configuration supporting StressChaos and IOChaos.

    Attributes:
        name (str): Experiment name.
        namespace (str): Kubernetes namespace.
        target (TargetSelector): Target pods.
        duration (str): Duration of the chaos.
        stress_cpu (StressCPUConfig | None): CPU stress config.
        stress_memory (StressMemoryConfig | None): Memory stress config.
        io_chaos (IOChaosConfig | None): I/O chaos config.
    """

    name: str
    namespace: str = "default"
    target: TargetSelector
    duration: str
    stress_cpu: StressCPUConfig | None = None
    stress_memory: StressMemoryConfig | None = None
    io_chaos: IOChaosConfig | None = None

    @model_validator(mode="before")
    def validate_at_least_one_fault(cls, values):
        if not any(
            values.get(key) for key in ["stress_cpu", "stress_memory", "io_chaos"]
        ):
            raise ValueError(
                "At least one of 'stress_cpu', 'stress_memory', or 'io_chaos' must be specified."
            )
        return values
