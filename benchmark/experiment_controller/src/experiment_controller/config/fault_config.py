from pydantic import BaseModel


class FaultSpecificConfig(BaseModel):
    pass


class TargetSelector(BaseModel):
    """
    Selector for target pods to apply chaos.

    Attributes:
        namespace (str):
            Kubernetes namespace of the target pods.
        label_selectors (dict[str, str]):
            Label selectors to match target pods.
    """

    environment: list[str]
    namespace: str
    label_selectors: dict[str, str]
