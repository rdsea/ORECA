from abc import ABC, abstractmethod

import pandas as pd


class BaseRCA(ABC):
    """Abstract base class for all Root Cause Analysis (RCA) methods."""

    @abstractmethod
    def __init__(self):
        """Initialize the RCA method."""
        pass

    @abstractmethod
    def run(
        self,
        dataset: pd.DataFrame,
        injection_time: int | None,
        top_k=5,
        **kwargs,
    ) -> list[tuple[str, float]]:
        """Run the RCA method on the given dataset.

        Args:
            dataset (pd.DataFrame): The input dataset containing time series data.
            injection_time (int | None): The timestamp when the fault was injected. Can be None if not applicable.
            top_k (int, optional): The number of top root causes to return. Defaults to 5.
            **kwargs: Additional keyword arguments specific to the RCA method.

        Returns:
            list[tuple[str, float]]: A list of tuples, where each tuple contains
                                     the name of a potential root cause (str) and its score (float),
                                     sorted in descending order of score.
        """
        pass
