from pydantic import BaseModel, model_validator


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
