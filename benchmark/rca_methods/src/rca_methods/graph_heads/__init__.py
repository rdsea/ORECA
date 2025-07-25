import numpy as np

# TODO: WIP


def finalize_directed_adj(adj: np.ndarray) -> np.ndarray:
    """Finalizes a directed adjacency matrix by converting various edge types to a standard directed format.

    In some causal discovery algorithms (like those in causallearn), the adjacency
    matrix can contain different values representing various edge types (e.g.,
    undirected, partially directed, bidirected, or edges with unknown orientation).
    This function converts these into a simplified directed adjacency matrix where:

    - `i --> j` is represented by `output_adj[j, i] = 1` and `output_adj[i, j] = 0`.
    - `i <-- j` is represented by `output_adj[j, i] = 0` and `output_adj[i, j] = 1`.
    - `i <-> j` (bidirected) is represented by `output_adj[j, i] = 1` and `output_adj[i, j] = 1`.

    The conversion rules are as follows:
    - `0` (no edge) remains `0`.
    - `1` (directed edge, e.g., `i --> j` or `i <-- j`) is converted to a standard directed edge.
    - `-1` (undirected edge, e.g., `i --- j`) is converted to a bidirected edge (`i <-> j`).
    - `2` (partially directed edge, e.g., `i o-> j` or `i o-o j` in FCI) are converted
      to directed or bidirected edges based on the combination.

    IMPORTANT NOTE:
    The edge direction in the output `adj` is from cause --> effect.
    Before passing to algorithms like PageRank, you might need to transpose the
    adjacency matrix (`adj.T`) to convert cause <-- effect relationships.

    Args:
        adj (np.ndarray): The input adjacency matrix, which may contain various edge type representations.

    Returns:
        np.ndarray: The finalized directed adjacency matrix with 0s and 1s.

    Raises:
        ValueError: If an unexpected combination of adjacency values is encountered.
    """
    output_adj = np.zeros_like(adj)
    for i in range(adj.shape[0]):
        for j in range(adj.shape[1]):
            # case 1: no edge: i j
            if adj[i, j] == adj[j, i] == 0:
                pass

            # case 2.1: fully directed i-->j
            elif adj[j, i] == 1 and adj[i, j] == -1:
                output_adj[j, i] = 1

            # case 2.2: fully directed i<--j
            elif adj[j, i] == -1 and adj[i, j] == 1:
                output_adj[i, j] = 1

            # case 2.3: fully directed i-->j, preprocessed case
            elif adj[j, i] == 1 and adj[i, j] == 0:
                output_adj[j, i] = 1

            # case 2.4: fully directed i<--j, preprocessed case
            elif adj[j, i] == 0 and adj[i, j] == 1:
                output_adj[i, j] = 1

            # case 3: i---j  to  i<->j
            elif adj[i, j] == adj[j, i] == -1:
                output_adj[i, j] = output_adj[j, i] = 1

            # case 4: i<->j  to  i<->j
            elif adj[i, j] == adj[j, i] == 1:
                output_adj[i, j] = output_adj[j, i] = 1

            # case 5.1: io->j  to  i-->j, in FCI, tricky
            elif adj[i, j] == 2 and adj[j, i] == 1:
                output_adj[j, i] = 1

            # case 5.2: i<-oj  to  i<--j, in FCI, tricky
            elif adj[i, j] == 1 and adj[j, i] == 2:
                output_adj[i, j] = 1

            # case 6: o-o  to  <->
            elif adj[i, j] == adj[j, i] == 2:
                output_adj[i, j] = output_adj[j, i] = 1

            else:
                raise ValueError(f"Unexpected value: {adj[i, j]=}, {adj[j, i]=}")

    return output_adj


# def finalize_undirected_adj(adj : np.ndarray) -> np.ndarray:
#     pass
