import numpy as np
from sknetwork.ranking import PageRank


def page_rank_preprocess(adj: np.ndarray) -> np.ndarray:
    """Preprocesses an adjacency matrix for PageRank calculation.

    This function converts various edge representations in an input adjacency matrix
    (e.g., from causal discovery algorithms) into a format suitable for PageRank,
    where `1` indicates a directed edge and `0` indicates no edge.

    The conversion rules are as follows:
    - `0` (no edge) remains `0`.
    - `-1` (undirected edge, e.g., `a --- b`) becomes a bidirected edge (`a <-> b`).
    - `1` (directed edge, e.g., `a -> b` or `a <- b`) is preserved as a directed edge.
    - `2` (partially directed edge, e.g., `a o-> b` or `a o-o b` in FCI) are converted
      to directed or bidirected edges based on the combination.

    Args:
        adj (np.ndarray): The input adjacency matrix, which may contain various edge type representations.

    Returns:
        np.ndarray: The preprocessed adjacency matrix with 0s and 1s, representing directed edges.

    Raises:
        ValueError: If an unexpected combination of adjacency values is encountered.
    """
    pr_input = np.zeros_like(adj)

    node_num = len(adj)

    for a in range(node_num):
        for b in range(node_num):
            # case 1 no edge: a b
            if adj[a, b] == adj[b, a] == 0:
                pass

            # case 2 undirected a -- b
            elif adj[a, b] == adj[b, a] == -1:
                pr_input[a, b] = pr_input[b, a] = 1

            # case 3 directed a -> b
            elif adj[a, b] == 1 and adj[b, a] == -1:
                pr_input[a, b] = 1
                # pr_input[b, a] = 0

            # case 4 directed a <- b
            elif adj[a, b] == -1 and adj[b, a] == 1:
                # pr_input[a, b] = 0
                pr_input[b, a] = 1
            elif adj[a, b] == 0 and adj[b, a] == 1:
                # already ok
                pr_input[a, b] = 0
                pr_input[b, a] = 1
            elif adj[a, b] == 1 and adj[b, a] == 0:
                # already ok
                pr_input[a, b] = 1
                pr_input[b, a] = 0
            elif adj[a, b] == 1 and adj[b, a] == 1:
                # a <-> b, in FCI
                pr_input[a, b] = 1
                pr_input[b, a] = 1
            elif adj[a, b] == 2 and adj[b, a] == 1:
                # a o-> b, in FCI
                # hmm, we will make it a->b
                pr_input[a, b] = 1
                pr_input[b, a] = 0
            elif adj[a, b] == 1 and adj[b, a] == 2:
                # a <-0 b, in FCI
                # hmm, we will make it a<-b
                pr_input[a, b] = 0
                pr_input[b, a] = 1

            elif adj[a, b] == 2 and adj[b, a] == 2:
                # a o-o b, in FCI
                # hmm, we will make it a<->b
                pr_input[a, b] = 1
                pr_input[b, a] = 1

            else:
                # 1 and 1 ?? what the hell?
                raise ValueError(f"Unexpected value: {adj[a, b]}, {adj[b, a]}")
    return pr_input


def page_rank(
    adj: np.ndarray,
    node_names: list[str] | None = None,
    damping_factor: float = 0.85,
    solver: str = "piteration",
    n_iter: int = 10,
    tol: float = 1e-6,
) -> list[tuple[str, float]]:
    """Calculates the PageRank scores for nodes in a graph represented by an adjacency matrix.

    Args:
        adj (np.ndarray): The adjacency matrix of the graph.
        node_names (list[str] | None, optional): A list of node names corresponding to the adjacency matrix. If None, default names will be generated. Defaults to None.
        damping_factor (float, optional): The damping factor for PageRank. Defaults to 0.85.
        solver (str, optional): The solver to use for PageRank calculation. Defaults to "piteration".
        n_iter (int, optional): The number of iterations for the solver. Defaults to 10.
        tol (float, optional): The tolerance for convergence. Defaults to 1e-6.

    Returns:
        list[tuple[str, float]]: A list of tuples, where each tuple contains the node name and its PageRank score, sorted in descending order of score.
    """
    if node_names is None:
        node_names = [f"X{i}" for i in range(len(adj))]

    pr_input = page_rank_preprocess(adj)

    pr = PageRank(damping_factor=damping_factor, solver=solver, n_iter=n_iter, tol=tol)

    # transpose before fit
    scores = pr.fit_transform(pr_input)

    # merge scores and node names, sort by scores
    output = list(zip(node_names, scores, strict=False))
    output.sort(key=lambda x: x[1], reverse=True)
    return output
