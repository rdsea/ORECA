from abc import ABC, abstractmethod

import pandas as pd


class BaseRCA(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(
        self, dataset: pd.DataFrame, top_k: int, injection_time: float | None, **kwargs
    ) -> list[tuple[str, float]]:
        pass
