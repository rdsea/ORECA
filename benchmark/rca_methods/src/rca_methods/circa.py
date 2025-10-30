import pandas as pd

from rca_methods.base_rca import BaseRCA
from rca_methods.graph_construction.pc import pc_default
from rca_methods.graph_heads.rht import rht
from rca_methods.io.time_series import drop_kpi


class Circa(BaseRCA):
    """Circa RCA method implementation."""

    def __init__(self, profile: bool = False):
        """Initializes the Circa RCA method."""
        super().__init__(profile)

    def _run(
        self, dataset: pd.DataFrame, injection_time: int | None, top_k=5, **kwargs
    ) -> list[tuple[str, float]]:
        """Runs the Circa RCA method.

        Args:
            dataset (pd.DataFrame): The input dataset.
            top_k (int): The number of top root causes to return.
            injection_time (float): The time of fault injection.

        Returns:
            list[tuple[str, float]]: A list of top_k root causes with their scores.
        """

        # dataset = preprocess(
        #     data=data,
        #     dataset=dataset,
        #     dk_select_useful=kwargs.get("dk_select_useful", False),
        # )

        dataset = drop_kpi(dataset)
        pc_input = dataset.drop(columns=["timestamp"])

        pc_input.columns.to_list()

        adj = pc_default(pc_input)
        ranks = rht(adj, injection_time, dataset)
        ranks = sorted(ranks, key=lambda x: x[1], reverse=True)
        return ranks[:top_k]
