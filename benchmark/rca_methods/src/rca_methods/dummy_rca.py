import random

import pandas as pd

from rca_methods.base_rca import BaseRCA


class DummyRCA(BaseRCA):
    """A dummy RCA method that returns random root causes."""

    def __init__(self):
        """Initializes the DummyRCA method."""
        pass

    def run(self, dataset: pd.DataFrame, top_k: int) -> list[tuple[str, float]]:
        """Runs the DummyRCA method.

        Args:
            dataset (pd.DataFrame): The input dataset (not used in this dummy implementation).
            top_k (int): The number of top root causes to return.

        Returns:
            list[tuple[str, float]]: A list of `top_k` randomly selected root causes with equal scores.
        """
        cols = dataset.columns.to_list()

        root_causes = random.sample(cols, top_k)
        return [(root_cause, 1 / top_k) for root_cause in root_causes]
