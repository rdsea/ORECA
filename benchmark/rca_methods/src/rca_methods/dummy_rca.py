import random

import pandas as pd

from rca_methods.base_rca import BaseRCA


class DummyRCA(BaseRCA):
    def __init__(self):
        pass

    def run(self, dataset: pd.DataFrame, top_k: int) -> list[tuple[str, float]]:
        cols = dataset.columns.to_list()

        root_causes = random.sample(cols, top_k)
        return [(root_cause, 1 / top_k) for root_cause in root_causes]
