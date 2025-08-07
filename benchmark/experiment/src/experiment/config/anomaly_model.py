from enum import Enum
from typing import NamedTuple

from experiment.config.fault_config import FaultSpecificConfig
from experiment.fault_controller.network import NetworkChaosConfig
from pydantic import BaseModel, field_validator, model_validator


class AnomalyCategory(Enum):
    """Enum for the category of an anomaly."""

    APPLICATION = "Application anomaly"
    WORKLOAD = "Workload anomaly"
    PLATFORM = "Platform anomaly"
    SYSTEM = "System anomaly"


class AnomalyInfo(NamedTuple):
    """A named tuple to hold information about an anomaly."""

    label: str
    category: AnomalyCategory


class AnomalyEnum(Enum):
    """Base enum for anomalies."""

    @property
    def label(self) -> str:
        """The label of the anomaly."""
        return self.value.label

    @property
    def category(self) -> AnomalyCategory:
        """The category of the anomaly."""
        return self.value.category


class ResourceHog(AnomalyEnum):
    """Enum for resource hog anomalies."""

    CPU = AnomalyInfo("Cpu", AnomalyCategory.PLATFORM)
    MEMORY = AnomalyInfo("Memory", AnomalyCategory.PLATFORM)
    IO = AnomalyInfo("Io", AnomalyCategory.PLATFORM)
    SOCKET = AnomalyInfo("Socket", AnomalyCategory.PLATFORM)


class NetworkFault(AnomalyEnum):
    """Enum for network faults."""

    DELAY = AnomalyInfo("Delay", AnomalyCategory.SYSTEM)
    LOSS = AnomalyInfo("Package loss", AnomalyCategory.SYSTEM)


class CodeLevelFault(AnomalyEnum):
    """Enum for code-level faults."""

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

FAULT_TYPE_TO_MODEL: dict[AnomalyEnum, type[FaultSpecificConfig]] = {
    NetworkFault.DELAY: NetworkChaosConfig,
    NetworkFault.LOSS: NetworkChaosConfig,
}


class FaultConfig(BaseModel):
    """Configuration for a fault."""

    name: str
    duration: str
    fault_type: AnomalyEnum
    fault_specific_config: BaseModel

    @field_validator("fault_type", mode="before")
    @classmethod
    def parse_fault_type(cls, v):
        """Parse the fault type from a string."""
        if isinstance(v, AnomalyEnum):
            return v
        try:
            return ALL_ANOMALY_ENUMS[v]
        except KeyError:
            raise ValueError(f"Unknown fault_type: {v}")

    @model_validator(mode="before")
    @classmethod
    def resolve_specific_config(cls, values):
        """Resolve the fault-specific configuration."""
        fault_type = values.get("fault_type")
        config_data = values.get("fault_specific_config")

        if isinstance(fault_type, str):
            try:
                fault_type = cls.parse_fault_type(fault_type)
            except ValueError:
                raise ValueError(f"Invalid fault_type: {fault_type}")

        model_cls = FAULT_TYPE_TO_MODEL.get(fault_type)
        if model_cls is None:
            raise ValueError(f"Unsupported fault_type: {fault_type}")

        if isinstance(config_data, dict):
            values["fault_specific_config"] = model_cls.model_validate(config_data)
        elif not isinstance(config_data, model_cls):
            raise TypeError(f"Expected config of type {model_cls.__name__}")

        values["fault_type"] = fault_type
        return values


class DockerWorkloadConfig(BaseModel):
    image: str
    args: dict[str, str] = {}


class ShellWorkloadConfig(BaseModel):
    script_path: str
    script_args: dict[str, str] = {}


class WorkloadConfig(BaseModel):
    type: str
    config: DockerWorkloadConfig | ShellWorkloadConfig

    @model_validator(mode="before")
    @classmethod
    def resolve_specific_config(cls, values):
        workload_type = values.get("type")
        config_data = values.get("config")

        if workload_type == "docker":
            model_cls = DockerWorkloadConfig
        elif workload_type == "shell":
            model_cls = ShellWorkloadConfig
        else:
            raise ValueError(f"Unsupported workload type: {workload_type}")

        if isinstance(config_data, dict):
            values["config"] = model_cls.model_validate(config_data)
        elif not isinstance(config_data, model_cls):
            raise TypeError(f"Expected config of type {model_cls.__name__}")

        return values


class RCAExperimentConfig(BaseModel):
    """Configuration for an RCA experiment."""

    experiment_name: str
    fault_config: FaultConfig
    # When to inject the anomaly, for example, 5, 10 minutes after starting load generation
    anomaly_injection_period: str
    list_of_generator: list[str]
    ssh_username: str
    workload: WorkloadConfig
