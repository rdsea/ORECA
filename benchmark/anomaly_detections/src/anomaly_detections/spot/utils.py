from typing import TypeVar

import numpy as np

_Template = TypeVar("_Template")


def moving_average(data: np.ndarray, window: int) -> np.ndarray:
    """Calculate the moving average of the given data.

    Args:
        data (np.ndarray): The data to calculate the moving average on.
        window (int): The size of the moving average window.

    Returns:
        np.ndarray: The moving average of the data.
    """
    mean: list[float] = []
    accumulation: float = data[:window].sum()
    mean.append(accumulation / window)
    for i in range(window, len(data)):
        accumulation = accumulation - data[i - window] + data[i]
        mean.append(accumulation / window)
    return np.array(mean)


def asc_key(value: _Template) -> _Template:
    """Return the value as is (ascending order).

    Args:
        value (_Template): The value.

    Returns:
        _Template: The value.
    """
    return value


def desc_key(value: _Template) -> _Template:
    """Return the negative of the value (descending order).

    Args:
        value (_Template): The value.

    Returns:
        _Template: The negative of the value.
    """
    return -value
