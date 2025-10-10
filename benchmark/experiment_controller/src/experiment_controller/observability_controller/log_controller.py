from pydantic import BaseModel


class LogControllerConfig(BaseModel):
    pass


class LogController:
    def __init__(self, config: LogControllerConfig):
        pass

    def apply(self):
        raise NotImplementedError("Log controller is not yet implemented")
