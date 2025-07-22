# pylint: disable=invalid-name
import logging

import numpy as np

from anomaly_detections.spot.extreme_value import ExtremeValue
from anomaly_detections.spot.spot_base import SPOTBase


class SPOT(SPOTBase):
    """
    This class allows to run SPOT algorithm on univariate dataset (upper-bound)
    """

    _plot_keys = ("thresholds",)

    def __init__(
        self, q: float = 1e-4, n_points: int = 10, logging_level: int = logging.WARNING
    ):
        """
        Constructor

        Parameters:
            q: Detection level (risk)
            n_points: maximum number of candidates for maximum likelihood (default : 10)
        """
        super().__init__(logging_level=logging_level)
        self._ev = ExtremeValue(q=q, n_points=n_points, logging_level=logging_level)

    def summary(self) -> dict:
        report = super().summary()
        report["Extreme Value"] = self._ev.summary()
        return report

    def initialize(self, level: float = 0.98):
        data = self._init_data
        level = level - np.floor(level)

        # t is fixed for the whole algorithm
        init_threshold = sorted(data)[int(level * data.size)]
        self._ev.initialize(data=data, init_threshold=init_threshold)
        self._num = data.size

    def run(self, with_alarm: bool = True) -> dict:
        """
        Run SPOT on the stream

        Parameters:
            with_alarm: If False, SPOT will adapt the threshold assuming
                there is no abnormal values (default = True)

        Returns:
            a dict:
                keys : 'thresholds' and 'alarms'

                'thresholds' contains the extreme quantiles and 'alarms' contains
                the indexes of the values which have triggered alarms

        """
        if self._num > self._init_data.size:
            self._logger.warning(
                "the algorithm seems to have already been run, "
                "you should initialize before running again"
            )
            return {}

        # list of the thresholds
        thresholds = []
        alarms = []
        # Loop over the stream
        for i, datum in enumerate(self._data):
            if (
                self._ev.run(datum, self._num, with_alarm=with_alarm)
                == ExtremeValue.Status.ALARM
            ):
                alarms.append(i)
            else:
                self._num += 1

            thresholds.append(self._ev.extreme_quantile)  # thresholds record

        return {"thresholds": thresholds, "alarms": alarms}
