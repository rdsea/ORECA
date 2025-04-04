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


def calc_pearson(matrix, method="default", zero_diag=True):
    """Calculate the pearson correlation between nodes

    Params:
        matrix: data of shape [N, T], N is node num, T is sample num
        method: method used, default for manually calculation,
            numpy for numpy implementation
        zero_diag:
                if zero the self correlation value (in diagonal position)
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


# relatoRank
def secondorder_randomwalk(
    m, epochs, start_node, label=None, walk_step=1000, print_trace=False
):
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


def guiyi(p):
    """Normalize matrix column-wise."""
    nextp = [[0 for i in range(len(p[0]))] for j in range(len(p))]
    for i in range(len(p)):
        for j in range(len(p[0])):
            line_sum = (np.sum(p, axis=1))[i]
            if line_sum == 0:
                break
            nextp[i][j] = p[i][j] / line_sum
    return nextp


def rela_to_rank(
    rela, access, rank_paces, frontend, beta=0.1, rho=0.3, print_trace=False
):
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
    inject_time=None,
    dataset=None,
    num_loop=None,
    sli=None,
    **kwargs,
):
    data = preprocess(
        data=data,
        dataset=dataset,
        dk_select_useful=kwargs.get("dk_select_useful", False),
    )
    np_data = data.to_numpy()
    node_names = data.columns.to_list()

    sli = node_names.index(sli)

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
        rela, dep_graph, 10, sli, beta=beta, rho=rho, print_trace=False
    )

    ranks = []
    for r in rank:  # (10, 1032.)
        r = r[0]  # 10
        # node_names[idx - 1]
        ranks.append(node_names[r - 1])

    return {
        "adj": adj,
        "node_names": node_names,
        "ranks": ranks,
    }
