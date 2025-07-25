import logging

import networkx as nx
import numpy as np
from tigramite import data_processing
from tigramite.independence_tests.parcorr import ParCorr
from tigramite.pcmci import PCMCI


class _ParCorr(ParCorr):
    """Wrap ParCorr to handle constant time series data.

    This class extends the ParCorr (Partial Correlation) class from Tigramite
    to provide a custom implementation of `_get_single_residuals` that can
    gracefully handle constant time series data by skipping them during standardization.
    """

    _logger_name = f"{ParCorr.__module__}.{ParCorr.__name__}"

    def _get_single_residuals(
        self,
        array: np.ndarray,
        target_var: int,
        standardize: bool = True,
        return_means: bool = False,
    ) -> np.ndarray:
        """Compute residuals for a single variable.

        Args:
            array (np.ndarray): The input data array.
            target_var (int): The index of the target variable.
            standardize (bool, optional): Whether to standardize the data. Defaults to True.
            return_means (bool, optional): Whether to return the means. Defaults to False.

        Returns:
            np.ndarray: The residuals.
        """
        y: np.ndarray = array[target_var, :]
        z: np.ndarray = np.copy(array[2:, :])

        # Standardize
        if standardize:
            y -= y.mean()
            std: np.ndarray = y.std()
            if std > 0:
                y /= std

            z -= z.mean(axis=1).reshape(-1, 1)
            std = z.std(axis=1)
            # Skip constant variables
            indexes: np.ndarray = np.where(std)[0]
            z = z[indexes, :] / std[indexes].reshape(-1, 1)
            if np.isnan(array).sum() != 0:
                raise ValueError("nans after standardizing, possibly constant array!")

        if z.shape[0] > 0:
            z = z.T
            try:
                beta_hat = np.linalg.lstsq(z, y, rcond=None)[0]
                mean = np.dot(z, beta_hat)
                resid = y - mean
            except np.linalg.LinAlgError as err:
                logging.getLogger(self._logger_name).warning(err, exc_info=True)
                resid = y
                mean = None
        else:
            resid = y
            mean = None

        if return_means:
            return (resid, mean)
        return resid


def _gather_tau(p_matrix: np.ndarray) -> np.ndarray:
    """Gathers the minimum p-value for each potential causal link from the p-matrix.

    Args:
        p_matrix (np.ndarray): The p-matrix from PCMCI, typically of shape (num_vars, num_vars, tau_max + 1).

    Returns:
        np.ndarray: A square matrix where each element [i, j] represents the minimum
                    p-value for the causal link from variable i to variable j across all lags.
    """
    num, result_num, _ = p_matrix.shape
    assert num == result_num

    link_matrix = []
    for reason in range(num):
        link_matrix.append([min(p_matrix[reason][result]) for result in range(num)])
    return np.array(link_matrix)


def pcmci(data, tau_max=3, alpha=0.2):
    """Applies the PCMCI algorithm for causal discovery.

    Args:
        data: The input data for causal discovery.
        tau_max (int, optional): The maximum time lag to consider. Defaults to 3.
        alpha (float, optional): The significance level for conditional independence tests. Defaults to 0.2.

    Returns:
        np.ndarray: The adjacency matrix representing the causal graph.
    """
    nodes = data.columns.to_list()

    dataframe = data_processing.DataFrame(data.to_numpy())

    m = PCMCI(
        dataframe=dataframe,
        cond_ind_test=_ParCorr(significance="analytic"),
        verbosity=0,
    )
    report = m.run_pcmci(
        tau_max=tau_max,
        pc_alpha=alpha,
        max_conds_dim=None,
    )

    matrix = _gather_tau(report["p_matrix"])

    """
    matrix: if matrix[i, j] is True, i may be one of the causes of j
    nodes: mapping from the matrix indexes to Nodes
    """
    # hmm..
    matrix = np.around(matrix, 3)

    graph = nx.DiGraph()
    graph.add_nodes_from(nodes)
    # graph.add_node(data.sli)
    graph.add_edges_from(
        (nodes[cause], nodes[effect])
        for cause, effect in zip(*np.where(matrix), strict=False)
    )

    adj = nx.adjacency_matrix(graph).todense()
    # adj = np.zeros((data.shape[1], data.shape[1]))
    # for n, neighbors in graph.adjacency():
    #     for i in neighbors.keys():
    #         adj[i, n] = 1

    return adj
