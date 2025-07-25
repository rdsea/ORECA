import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests


def granger(
    data: pd.DataFrame,
    maxlag: int | None = None,
    p_val_threshold: float = 0.05,
    test: str | None = None,
) -> np.ndarray:
    """Performs Granger causality tests to infer causal relationships between time series.

    Args:
        data (pd.DataFrame): The input time series data.
        maxlag (int | None, optional): The maximum number of lags to test. Defaults to 3.
        p_val_threshold (float, optional): The p-value threshold for determining causality. Defaults to 0.05.
        test (str | None, optional): The type of test to use (e.g., "ssr_ftest", "ssr_chi2test", "lrtest", "params_ftest"). If None, uses the average p-value from all tests. Defaults to None.

    Returns:
        np.ndarray: An adjacency matrix where adj[i, j] = 1 if j Granger-causes i, and 0 otherwise.
    """
    assert test in [None, "ssr_ftest", "ssr_chi2test", "lrtest", "params_ftest"]

    # data: pandas dataframe
    if maxlag is None:
        maxlag = 3
    node_names = data.columns.to_list()
    adj = np.zeros((len(node_names), len(node_names)))

    for i in range(len(node_names)):
        for j in range(len(node_names)):
            if i == j:
                continue
            # test j -> i
            output = grangercausalitytests(
                data[[node_names[i], node_names[j]]], maxlag, verbose=False
            )
            caused = False
            for _time_lag, out in output.items():
                out = out[0]

                if test is None:
                    avg_p_val = sum([v[1] for k, v in out.items()]) / len(out)
                else:
                    avg_p_val = out[test][1]

                if avg_p_val < p_val_threshold:  # average p-value
                    caused = True
                    break
            if caused:
                adj[i, j] = 1
    return adj
