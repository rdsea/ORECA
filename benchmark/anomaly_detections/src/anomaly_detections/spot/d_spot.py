import logging

import numpy as np

from anomaly_detections.spot.extreme_value import ExtremeValue
from anomaly_detections.spot.spot import SPOT
from anomaly_detections.spot.utils import moving_average


class DSPOT(SPOT):
    """
    This class allows to run DSPOT algorithm on univariate dataset (upper-bound)
    """

    def __init__(
        self,
        q: float = 1e-4,
        n_points: int = 10,
        depth: int = 10,
        logging_level: int = logging.WARNING,
    ):
        """
        Constructor

        Parameters:
            q: Detection level (risk)
            n_points: maximum number of candidates for maximum likelihood (default : 10)
            depth: Number of observations to compute the moving average
        """
        super().__init__(q=q, n_points=n_points, logging_level=logging_level)
        self._depth = depth

    def initialize(self, level: float = 0.98):
        data: np.ndarray = (
            self._init_data[self._depth :]
            - moving_average(self._init_data, self._depth)[:-1]
        )
        level = level - np.floor(level)

        # t is fixed for the whole algorithm
        init_threshold = sorted(data)[int(level * data.size)]
        self._ev.initialize(data=data, init_threshold=init_threshold)
        self._num = data.size

    def run(self, with_alarm: bool = True) -> dict:
        if self._num > self._init_data.size:
            self._logger.warning(
                "the algorithm seems to have already been run, "
                "you should initialize before running again"
            )
            return {}

        # actual normal window
        window: np.ndarray = self._init_data[-self._depth :]

        # list of the thresholds
        thresholds = []
        alarms = []
        # Loop over the stream
        for i, datum in enumerate(self._data):
            mean = window.mean()
            if (
                self._ev.run(datum - mean, self._num, with_alarm=with_alarm)
                == ExtremeValue.Status.ALARM
            ):
                alarms.append(i)
            else:
                self._num += 1
                window = np.append(window[1:], datum)

            thresholds.append(self._ev.extreme_quantile + mean)  # thresholds record

        return {"thresholds": thresholds, "alarms": alarms}
