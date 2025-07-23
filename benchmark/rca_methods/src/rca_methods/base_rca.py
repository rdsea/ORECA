from abc import ABC, abstractmethod

import pandas as pd


class BaseRCA(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(
        self,
        dataset: pd.DataFrame,
        injection_time: int | None,
        top_k=5,
        **kwargs,
    ) -> list[tuple[str, float]]:
        pass
