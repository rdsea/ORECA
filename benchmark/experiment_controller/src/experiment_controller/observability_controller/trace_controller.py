from pydantic import BaseModel


class TraceControllerConfig(BaseModel):
    pass


class TraceController:
    def __init__(self, config: TraceControllerConfig):
        pass

    def apply(self):
        raise NotImplementedError("Trace controller is not yet implemented")
