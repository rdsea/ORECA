from collections.abc import Callable
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, model_serializer, model_validator

from experiment_controller.logger import logger
from experiment_controller.script_runner import ScriptRunner


class ElasticType(Enum):
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"


class ElasticCategory(BaseModel):
    name: str
    type: ElasticType
    active: bool
    how_to_activate: Callable | Path | None = None
    how_to_deactivate: Callable | Path | None = None

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Serialize the model to a dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "active": self.active,
            "how_to_activate": str(self.how_to_activate)
            if isinstance(self.how_to_activate, Path)
            else None,
            "how_to_deactivate": str(self.how_to_deactivate)
            if isinstance(self.how_to_deactivate, Path)
            else None,
        }


class ElasticApplication(ElasticCategory):
    type: ElasticType = ElasticType.APPLICATION


class ElasticInfrastructure(ElasticCategory):
    type: ElasticType = ElasticType.INFRASTRUCTURE


class ElasticConfig(BaseModel):
    environment: dict[str, list[ElasticInfrastructure | ElasticApplication]]

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Serialize the model to a dictionary."""
        return {
            "environment": {
                env_name: [elastic.model_dump() for elastic in elastic_list]
                for env_name, elastic_list in self.environment.items()
            }
        }

    @model_validator(mode="before")
    @classmethod
    def resolve_specific_config(cls, values):
        envs = values.get("environment")
        if not envs:
            return values

        resolved_envs: dict[str, list[ElasticCategory]] = {}

        for env_name, elastic_used in envs.items():
            resolved_elastic_used = []
            for config_data in elastic_used:
                elastic_type = (
                    config_data.get("type")
                    if isinstance(config_data, dict)
                    else getattr(config_data, "type", None)
                )

                if (
                    elastic_type == "application"
                    or elastic_type == ElasticType.APPLICATION
                ):
                    model_cls = ElasticApplication
                elif (
                    elastic_type == "infrastructure"
                    or elastic_type == ElasticType.INFRASTRUCTURE
                ):
                    model_cls = ElasticInfrastructure
                else:
                    raise ValueError(f"Unsupported elastic type: {elastic_type}")

                if isinstance(config_data, dict):
                    resolved_elastic_used.append(model_cls.model_validate(config_data))
                elif not isinstance(config_data, model_cls):
                    raise TypeError(f"Expected config of type {model_cls.__name__}")
                else:
                    resolved_elastic_used.append(config_data)

            resolved_envs[env_name] = resolved_elastic_used

        values["environment"] = resolved_envs
        return values


class ElasticController:
    def __init__(self, config: ElasticConfig):
        self.config = config
        self.script_runner = ScriptRunner()

    def activate_all(self):
        failed_elastic_config: list[ElasticCategory] = []
        for environment in self.config.environment:
            # TODO: apply per environment
            for elastic_config in self.config.environment[environment]:
                if elastic_config.how_to_activate and elastic_config.active:
                    try:
                        if isinstance(elastic_config.how_to_activate, Callable):
                            elastic_config.how_to_activate()
                        else:
                            self.script_runner.run_retry(
                                str(elastic_config.how_to_activate)
                            )
                    except Exception:
                        logger.exception(f"{elastic_config.name} error")
                        failed_elastic_config.append(elastic_config)
                    logger.info(f"Activate {elastic_config.name} config")
            if not failed_elastic_config:
                logger.info("All elastic config activate successfully")
            else:
                for elastic_config in failed_elastic_config:
                    logger.info(f"{elastic_config.name} config activate failed")
                raise RuntimeError("Failed to activate elastic config")

    def deactivate_all(self):
        failed_elastic_config: list[ElasticCategory] = []
        for environment in self.config.environment:
            # TODO: apply per environment
            for elastic_config in self.config.environment[environment]:
                if elastic_config.how_to_deactivate and elastic_config.active:
                    try:
                        if isinstance(elastic_config.how_to_deactivate, Callable):
                            elastic_config.how_to_deactivate()
                        else:
                            self.script_runner.run_retry(
                                str(elastic_config.how_to_deactivate)
                            )
                    except Exception:
                        logger.exception(f"{elastic_config.name} deactivate error")
                        failed_elastic_config.append(elastic_config)
                    logger.info(f"Deactivate {elastic_config.name} config")
            if not failed_elastic_config:
                logger.info("All elastic config deactivate successfully")
            else:
                for elastic_config in failed_elastic_config:
                    logger.info(f"{elastic_config.name} config deactivate failed")
