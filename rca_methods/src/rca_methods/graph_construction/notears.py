import numpy as np
import pandas as pd
from castle.algorithms import Notears


def notears(data: pd.DataFrame):
    # notears learn
    nt = Notears()
    nt.learn(np.array(data))

    return np.array(nt.causal_matrix)
