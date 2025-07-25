import numpy as np
import pandas as pd
from causalai.application import RootCauseDetector
from causalai.application.common import rca_preprocess

from rca_methods.base_rca import BaseRCA


def drop_constant_column(df: pd.DataFrame) -> pd.DataFrame:
    """Drops columns from a DataFrame that have only one unique value (constant columns)."""
    for col in df.columns:
        if df[col].nunique() == 1:
            df.drop(col, axis=1, inplace=True)
    return df


def causalai(
    data: pd.DataFrame,
    inject_time: int | None = None,
    dataset: str | None = None,
    with_bg: bool = False,
    args: dict | None = None,
    **kwargs,
) -> dict:
    """Runs the CausalAI root cause analysis method.

    Args:
        data (pd.DataFrame): The input dataset.
        inject_time (int | None, optional): The injection time. Defaults to None.
        dataset (str | None, optional): The dataset name. Defaults to None.
        with_bg (bool, optional): Whether to include background knowledge. Defaults to False.
        args (dict | None, optional): Additional arguments. Defaults to None.

    Returns:
        dict: A dictionary containing the ranks of the root causes.
    """
    data = drop_constant_column(data)

    if "time" not in data.columns:
        data["time"] = np.arange(len(data))

    df_normal = data[data["time"] < inject_time]
    df_abnormal = data[data["time"] >= inject_time]

    lower_level_columns = [c for c in df_normal.columns if c not in ["time"]]
    upper_level_metric = data["time"].tolist()
    df_normal = df_normal[lower_level_columns]
    df_abnormal = df_abnormal[lower_level_columns]

    data_obj, var_names = rca_preprocess(
        data=[df_normal, df_abnormal],
        time_metric=upper_level_metric,
        time_metric_name="time",
    )

    model = RootCauseDetector(
        data_obj=data_obj,
        var_names=var_names,
        time_metric_name="time",
        prior_knowledge=None,
    )

    root_causes, graph = model.run(
        pvalue_thres=0.001, max_condition_set_size=4, return_graph=True
    )

    return {"ranks": list(root_causes)}


class CausalAI(BaseRCA):
    """CausalAI RCA method implementation."""

    def __init__(self):
        """Initializes the CausalAI RCA method."""
        pass

    def run(
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
        data = drop_constant_column(dataset)

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
            time_metric_name="time",
        )

        model = RootCauseDetector(
            data_obj=data_obj,
            var_names=var_names,
            time_metric_name="time",
            prior_knowledge=None,
        )

        root_causes, _ = model.run(
            pvalue_thres=0.001, max_condition_set_size=4, return_graph=True
        )
        print(root_causes)
        return {"ranks": list(root_causes)}
