from collections.abc import Callable

from pydantic import BaseModel


class ElasticCategory(BaseModel):
    name: str
    active: bool
    how_to_activate: Callable
    how_to_deactivate: Callable


class ElasticApplication(ElasticCategory):
    pass


class ElasticInfrastructure(ElasticCategory):
    pass


class ElasticControllerConfig(ElasticCategory):
    elastic_used: list[ElasticInfrastructure | ElasticApplication]


class ElasticController:
    def __init__(self, config: ElasticControllerConfig):
        pass
