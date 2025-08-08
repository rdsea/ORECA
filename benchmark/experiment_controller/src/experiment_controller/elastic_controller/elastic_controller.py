from collections.abc import Callable

from pydantic import BaseModel

from experiment_controller.logger import logger


class ElasticCategory(BaseModel):
    name: str
    active: bool
    how_to_activate: Callable | None
    how_to_deactivate: Callable | None


class ElasticApplication(ElasticCategory):
    pass


class ElasticInfrastructure(ElasticCategory):
    pass


class ElasticControllerConfig(ElasticCategory):
    elastic_used: list[ElasticInfrastructure | ElasticApplication]


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
        if failed_elastic_config:
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
        if failed_elastic_config:
            logger.info("All elastic config deactivate successfully")
        else:
            for elastic_config in failed_elastic_config:
                logger.info(f"{elastic_config.name} config deactivate failed")
