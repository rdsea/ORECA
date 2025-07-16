from typing import TypeVar

import numpy as np

_Template = TypeVar("_Template")


def moving_average(data: np.ndarray, window: int) -> np.ndarray:
    """
    Moving average of the given data
    """
    mean: list[float] = []
    accumulation: float = data[:window].sum()
    mean.append(accumulation / window)
    for i in range(window, len(data)):
        accumulation = accumulation - data[i - window] + data[i]
        mean.append(accumulation / window)
    return np.array(mean)


def asc_key(value: _Template) -> _Template:
    return value


def desc_key(value: _Template) -> _Template:
    return -value
