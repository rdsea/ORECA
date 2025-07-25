# take from https://github.com/PanYicheng/dycause_rca/tree/main
# with update
import math

import numpy as np
import pandas as pd
from causallearn.search.ConstraintBased.PC import pc

from rca_methods.graph_heads import finalize_directed_adj
from rca_methods.io.time_series import (
    preprocess,
)


def calc_pearson(
    matrix: np.ndarray, method: str = "default", zero_diag: bool = True
) -> list[list[float]]:
    """Calculate the Pearson correlation between nodes.

    Args:
        matrix (np.ndarray): Data of shape [N, T], where N is the number of nodes and T is the number of samples.
        method (str, optional): Method used for calculation. 'default' for manual calculation, 'numpy' for NumPy implementation. Defaults to "default".
        zero_diag (bool, optional): If True, the self-correlation value (in diagonal position) will be set to 0.0. Defaults to True.

    Returns:
        list[list[float]]: A 2D list representing the Pearson correlation matrix.
    """
    if method == "numpy":
        res = np.corrcoef(np.array(matrix))
        if zero_diag:
            for i in range(res.shape[0]):
                res[i, i] = 0.0
        res = res.tolist()
    else:
        nrows = len(matrix)
        ncols = len(matrix[0])
        n = ncols * 1.0
        res = [[0 for i in range(nrows)] for j in range(nrows)]
        for i in range(nrows):
            idx = i + 1
            for j in range(idx, nrows):
                a = b = c = f = e = 0
                for k in range(0, ncols):
                    a += matrix[i][k] * matrix[j][k]  # sigma xy
                    b += matrix[i][k]  # sigma x
                    c += matrix[j][k]  # sigma y
                    e += matrix[i][k] * matrix[i][k]  # sigma xx
                    f += matrix[j][k] * matrix[j][k]  # sigma yy

                para1 = a
                para2 = b * c / n
                para3 = e
                para4 = b * b / n
                para5 = f
                para6 = c * c / n

                r1 = para1 - para2
                r2 = (para3 - para4) * (para5 - para6)
                r2 = math.sqrt(r2)
                r = 1.0 * r1 / r2
                res[i][j] = res[j][i] = r * 1.00000
        if not zero_diag:
            for i in range(nrows):
                for j in range(nrows):
                    res[i][j] = 1.0
    return res


def secondorder_randomwalk(
    m: np.ndarray,
    epochs: int,
    start_node: int,
    label: list | None = None,
    walk_step: int = 1000,
    print_trace: bool = False,
) -> list[tuple[int, float]]:
    """Performs a second-order random walk on a given transition matrix.

    Args:
        m (np.ndarray): The transition matrix.
        epochs (int): The number of epochs to run the random walk.
        start_node (int): The starting node for the random walk.
        label (list | None, optional): Labels for the nodes. Defaults to None.
        walk_step (int, optional): The number of steps in each walk. Defaults to 1000.
        print_trace (bool, optional): If True, prints the trace of the walk. Defaults to False.

    Returns:
        list[tuple[int, float]]: A list of tuples, where each tuple contains the node label and its score, sorted by score in descending order.
    """
    if label is None:
        label = []
    n = m.shape[0]
    score = np.zeros([n])
    for _epoch in range(epochs):
        previous = start_node - 1
        current = start_node - 1
        if print_trace:
            print(f"\n{current + 1:2d}", end="->")
        for _step in range(walk_step):
            if np.sum(m[previous, current]) == 0:
                break
            next_node = np.random.choice(range(n), p=m[previous, current])
            if print_trace:
                print(f"{current + 1:2d}", end="->")
            score[next_node] += 1
            previous = current
            current = next_node
    score_list = list(zip(label, score, strict=False))
    score_list.sort(key=lambda x: x[1], reverse=True)
    return score_list


def guiyi(p: list[list[float]]) -> list[list[float]]:
    """Normalize matrix column-wise.

    Args:
        p (list[list[float]]): The input matrix.

    Returns:
        list[list[float]]: The column-wise normalized matrix.
    """
    nextp = [[0 for _ in range(len(p[0]))] for _ in range(len(p))]
    for i in range(len(p)):
        line_sum = (np.sum(p, axis=1))[i]
        if line_sum == 0:
            # Handle the case where the sum of the row is zero to avoid division by zero
            # You might want to set nextp[i][j] to 0 or some other value based on your logic
            continue
        for j in range(len(p[0])):
            nextp[i][j] = p[i][j] / line_sum
    return nextp


def rela_to_rank(
    rela: list[list[float]],
    access: np.ndarray,
    rank_paces: int,
    frontend: int,
    beta: float = 0.1,
    rho: float = 0.3,
    print_trace: bool = False,
) -> tuple[list[tuple[int, float]], list[list[float]], np.ndarray]:
    """Calculates the relational ranking based on a second-order random walk.

    Args:
        rela (list[list[float]]): The relational matrix.
        access (np.ndarray): The access matrix.
        rank_paces (int): The number of paces for the random walk.
        frontend (int): The frontend node.
        beta (float, optional): Beta parameter. Defaults to 0.1.
        rho (float, optional): Rho parameter. Defaults to 0.3.
        print_trace (bool, optional): If True, prints the trace of the walk. Defaults to False.

    Returns:
        tuple[list[tuple[int, float]], list[list[float]], np.ndarray]: A tuple containing
            - The ranked list of nodes.
            - The normalized probability matrix.
            - The second-order transition matrix.
    """
    n = len(access)
    s = rela[frontend - 1]
    p = [[0 for col in range(n)] for row in range(n)]
    for i in range(n):
        for j in range(n):
            if access[i][j] != 0:
                p[i][j] = abs(s[j])
    p = guiyi(p)
    m = np.zeros([n, n, n])
    # Forward probability
    for i in range(n):
        for j in range(n):
            if access[i][j] > 0:
                for k in range(n):
                    m[k, i, j] = (1 - beta) * p[k][i] + beta * p[i][j]
    # Normalize w.r.t. out nodes
    for k in range(n):
        for i in range(n):
            if np.sum(m[k, i]) > 0:
                m[k, i] = m[k, i] / np.sum(m[k, i])
    # Add backward edges
    for k in range(n):
        for i in range(n):
            in_inds = []
            for j in range(n):
                if access[i][j] == 0 and access[j][i] != 0:
                    m[k, i, j] = rho * ((1 - beta) * p[k][i] + beta * p[j][i])
                    in_inds.append(j)
            # Normalize wrt in nodes
            if np.sum(m[k, i, in_inds]) > 0:
                m[k, i, in_inds] /= np.sum(m[k, i, in_inds])
    # Add self edges
    for k in range(n):
        for i in range(n):
            if m[k, i, i] == 0:
                in_out_node = list(range(n))
                in_out_node.remove(i)
                m[k, i, i] = max(0, s[i] - max(m[k, i, in_out_node]))
    # Normalize all
    for k in range(n):
        for i in range(n):
            if np.sum(m[k, i]) > 0:
                m[k, i] /= np.sum(m[k, i])

    label = list(range(1, n + 1))
    random_walk_list = secondorder_randomwalk(
        m, rank_paces, frontend, label, print_trace=print_trace
    )
    return random_walk_list, p, m


def cloudranger(
    data: pd.DataFrame,
    inject_time: int | None = None,
    dataset: str | None = None,
    num_loop: int | None = None,
    sli: str | None = None,
    **kwargs,
) -> dict:
    """Performs root cause analysis using the CloudRanger method.

    Args:
        data (pd.DataFrame): The input data.
        inject_time (int | None, optional): The injection time. Defaults to None.
        dataset (str | None, optional): The dataset name. Defaults to None.
        num_loop (int | None, optional): Number of loops. Defaults to None.
        sli (str | None, optional): Service Level Indicator. Defaults to None.

    Returns:
        dict: A dictionary containing the adjacency matrix, node names, and ranked root causes.
    """
    data = preprocess(
        data=data,
        dataset=dataset,
        dk_select_useful=kwargs.get("dk_select_useful", False),
    )
    np_data = data.to_numpy()
    node_names = data.columns.to_list()

    sli_index = (
        node_names.index(sli) if sli else 0
    )  # Default to first node if sli is None

    # params
    pc_alpha = 0.1
    beta = 0.3
    rho = 0.2

    # graph construction, pc
    cg = pc(np_data.astype(float), show_progress=False, alpha=pc_alpha)
    adj = cg.G.graph

    # scoring
    rela = calc_pearson(np_data.T, method="numpy", zero_diag=False)
    dep_graph = finalize_directed_adj(adj).T

    rank, _, _ = rela_to_rank(
        rela, dep_graph, 10, sli_index + 1, beta=beta, rho=rho, print_trace=False
    )

    ranks = []
    for r in rank:  # (10, 1032.)
        r_idx = r[0] - 1  # Adjust for 0-based indexing
        if 0 <= r_idx < len(node_names):
            ranks.append(node_names[r_idx])
        else:
            # Handle cases where r[0] might be out of bounds
            print(f"Warning: Node index {r_idx} out of bounds for node_names.")

    return {
        "adj": adj,
        "node_names": node_names,
        "ranks": ranks,
    }
