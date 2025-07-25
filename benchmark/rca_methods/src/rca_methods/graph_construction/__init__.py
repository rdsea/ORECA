import numpy as np

# from .fci import fci_default
# from .ges import ges
# from .granger import granger
# from .lingam import DirectLiNGAM, ICALiNGAM
# from .pc import pc_default


def normalize_adj(adj: np.ndarray) -> np.ndarray:
    """Normalizes an adjacency matrix based on different edge types.

    This function processes an adjacency matrix where values represent different
    types of relationships (e.g., no edge, undirected, directed, FCI-specific).
    It converts these into a normalized adjacency matrix where 1 indicates an
    edge and 0 indicates no edge.

    Args:
        adj (np.ndarray): The input adjacency matrix.

    Returns:
        np.ndarray: The normalized adjacency matrix.

    Raises:
        ValueError: If an unexpected adjacency value combination is encountered.
    """
    norm_adj = np.zeros_like(adj)

    node_num = len(adj)

    for a in range(node_num):
        for b in range(node_num):
            # case 1 no edge: a b
            if adj[a, b] == adj[b, a] == 0:
                pass

            # case 2 undirected a -- b
            elif adj[a, b] == adj[b, a] == -1:
                norm_adj[a, b] = norm_adj[b, a] = 1

            # case 3 directed a -> b
            elif adj[a, b] == 1 and adj[b, a] == -1:
                norm_adj[a, b] = 1
                # pr_input[b, a] = 0

            # case 4 directed a <- b
            elif adj[a, b] == -1 and adj[b, a] == 1:
                # pr_input[a, b] = 0
                norm_adj[b, a] = 1
            elif adj[a, b] == 0 and adj[b, a] == 1:
                # already ok
                norm_adj[a, b] = 0
                norm_adj[b, a] = 1
            elif adj[a, b] == 1 and adj[b, a] == 0:
                # already ok
                norm_adj[a, b] = 1
                norm_adj[b, a] = 0
            elif adj[a, b] == 1 and adj[b, a] == 1:
                # a <-> b, in FCI
                norm_adj[a, b] = 1
                norm_adj[b, a] = 1
            elif adj[a, b] == 2 and adj[b, a] == 1:
                # a o-> b, in FCI
                # hmm, we will make it a->b
                norm_adj[a, b] = 1
                norm_adj[b, a] = 0
            elif adj[a, b] == 1 and adj[b, a] == 2:
                # a <-0 b, in FCI
                # hmm, we will make it a<-b
                norm_adj[a, b] = 0
                norm_adj[b, a] = 1

            elif adj[a, b] == 2 and adj[b, a] == 2:
                # a o-o b, in FCI
                # hmm, we will make it a<->b
                norm_adj[a, b] = 1
                norm_adj[b, a] = 1

            else:
                # 1 and 1 ?? what the hell?
                raise ValueError(f"Unexpected value: {adj[a, b]}, {adj[b, a]}")
    return norm_adj
