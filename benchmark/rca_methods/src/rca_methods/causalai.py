import pandas as pd
from causalai.application import RootCauseDetector
from causalai.application.common import rca_preprocess

from rca_methods.base_rca import BaseRCA
from rca_methods.io.time_series import drop_kpi


def drop_constant_column(df: pd.DataFrame) -> pd.DataFrame:
    """Drops columns from a DataFrame that have only one unique value (constant columns)."""
    for col in df.columns:
        if df[col].nunique() == 1:
            df.drop(col, axis=1, inplace=True)
    return df


class CausalAI(BaseRCA):
    """CausalAI RCA method implementation."""

    def __init__(self, profile: bool = False):
        """Initializes the CausalAI RCA method."""
        super().__init__(profile)

    def _run(
        self,
        dataset: pd.DataFrame,
        injection_time: int | None,
        top_k=5,
        **kwargs,
    ) -> list[tuple[str, float]]:
        """Runs the CausalAI RCA method.

        Args:
            dataset (pd.DataFrame): The input dataset.
            injection_time (int | None): The time of fault injection.
            top_k (int, optional): The number of top root causes to return. Defaults to 5.

        Returns:
            list[tuple[str, float]]: A list of tuples, where each tuple contains
                                     the name of a potential root cause (str) and its score (float).
        """
        dataset = drop_kpi(dataset)
        data = drop_constant_column(dataset)
        data.drop(columns=["timestamp"], inplace=True)
        # if "timestamp" not in data.columns:
        #     data["time"] = np.arange(len(data))

        df_normal = data[data["timestamp"] < injection_time]
        df_abnormal = data[data["timestamp"] >= injection_time]

        lower_level_columns = [c for c in df_normal.columns if c not in ["timestamp"]]
        upper_level_metric = data["timestamp"].tolist()
        df_normal = df_normal[lower_level_columns]
        df_abnormal = df_abnormal[lower_level_columns]

        data_obj, var_names = rca_preprocess(
            data=[df_normal, df_abnormal],
            time_metric=upper_level_metric,
            time_metric_name="timestamp",
        )

        model = RootCauseDetector(
            data_obj=data_obj,
            var_names=var_names,
            time_metric_name="timestamp",
            prior_knowledge=None,
        )
        root_causes, _ = model.run(
            pvalue_thres=0.001, max_condition_set_size=4, return_graph=True
        )
        return list(root_causes)[:top_k]
