from collections.abc import Callable
from enum import Enum

from pydantic import BaseModel, model_validator

from experiment_controller.logger import logger


class ElasticType(Enum):
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"


class ElasticCategory(BaseModel):
    name: str
    type: ElasticType
    active: bool
    how_to_activate: Callable | None = None
    how_to_deactivate: Callable | None = None


class ElasticApplication(ElasticCategory):
    type: ElasticType = ElasticType.APPLICATION


class ElasticInfrastructure(ElasticCategory):
    type: ElasticType = ElasticType.INFRASTRUCTURE


class ElasticControllerConfig(BaseModel):
    elastic_used: list[ElasticInfrastructure | ElasticApplication]

    @model_validator(mode="before")
    @classmethod
    def resolve_specific_config(cls, values):
        elastic_used = values.get("elastic_used")
        if elastic_used:
            resolved_elastic_used = []
            for config_data in elastic_used:
                elastic_type = config_data.get("type")
                if elastic_type == "application":
                    model_cls = ElasticApplication
                elif elastic_type == "infrastructure":
                    model_cls = ElasticInfrastructure
                else:
                    raise ValueError(f"Unsupported elastic type: {elastic_type}")

                if isinstance(config_data, dict):
                    resolved_elastic_used.append(model_cls.model_validate(config_data))
                elif not isinstance(config_data, model_cls):
                    raise TypeError(f"Expected config of type {model_cls.__name__}")
            values["elastic_used"] = resolved_elastic_used
        return values


class ElasticController:
    def __init__(self, config: ElasticControllerConfig):
        self.config = config

    def activate_all(self):
        failed_elastic_config: list[ElasticCategory] = []
        for elastic_config in self.config.elastic_used:
            if elastic_config.how_to_activate:
                try:
                    elastic_config.how_to_activate()
                except Exception:
                    logger.exception(f"{elastic_config.name} error")
                    failed_elastic_config.append(elastic_config)
                logger.info(f"Activate {elastic_config.name} config")
        if not failed_elastic_config:
            logger.info("All elastic config activate successfully")
        else:
            for elastic_config in failed_elastic_config:
                logger.info(f"{elastic_config.name} config activate failed")

    def deactivate_all(self):
        failed_elastic_config: list[ElasticCategory] = []
        for elastic_config in self.config.elastic_used:
            if elastic_config.how_to_deactivate:
                try:
                    elastic_config.how_to_deactivate()
                except Exception:
                    logger.exception(f"{elastic_config.name} deactivate error")
                    failed_elastic_config.append(elastic_config)
                logger.info(f"Deactivate {elastic_config.name} config")
        if not failed_elastic_config:
            logger.info("All elastic config deactivate successfully")
        else:
            for elastic_config in failed_elastic_config:
                logger.info(f"{elastic_config.name} config deactivate failed")
