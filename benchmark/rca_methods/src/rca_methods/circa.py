import pandas as pd

from rca_methods.base_rca import BaseRCA
from rca_methods.graph_construction.pc import pc_default
from rca_methods.graph_heads.rht import rht


class Circa(BaseRCA):
    def __init__(self):
        pass

    def run(
        self, dataset: pd.DataFrame, top_k: int, injection_time: float, **kwargs
    ) -> list[tuple[str, float]]:
        time_col = dataset["time"]

        dataset["time"] = time_col

        # dataset = preprocess(
        #     data=data,
        #     dataset=dataset,
        #     dk_select_useful=kwargs.get("dk_select_useful", False),
        # )

        pc_input = dataset.drop(columns=["time"])
        pc_input.columns.to_list()

        adj = pc_default(pc_input, dataset="ob")
        ranks = rht(adj, injection_time, dataset)
        ranks = sorted(ranks, key=lambda x: x[1], reverse=True)
        ranks = [x[0] for x in ranks]
        return ranks[:top_k]
