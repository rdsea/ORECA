import numpy as np
import pandas as pd
from castle.algorithms import Notears


def notears(data: pd.DataFrame) -> np.ndarray:
    """Learns the causal graph using the Notears algorithm.

    Args:
        data (pd.DataFrame): The input data for causal discovery.

    Returns:
        np.ndarray: The learned causal matrix (adjacency matrix).
    """
    nt = Notears()
    nt.learn(np.array(data))

    return np.array(nt.causal_matrix)
