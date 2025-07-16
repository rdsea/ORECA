import logging

import numpy as np

from anomaly_detections.spot.extreme_value import ExtremeValue
from anomaly_detections.spot.spot_base import SPOTBase
from anomaly_detections.spot.utils import asc_key, desc_key


class BiSPOT(SPOTBase):
    """
    This class allows to run biSPOT algorithm on univariate dataset (upper and lower bounds)
    """

    _plot_keys = ("upper_thresholds", "lower_thresholds")

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
        self._ev = {
            "upper": ExtremeValue(
                q=q, n_points=n_points, key=asc_key, logging_level=logging_level
            ),
            "lower": ExtremeValue(
                q=q, n_points=n_points, key=desc_key, logging_level=logging_level
            ),
        }

    def summary(self) -> dict:
        report = super().summary()
        report["upper Extreme Value"] = self._ev["upper"].summary()
        report["lower Extreme Value"] = self._ev["lower"].summary()
        return report

    def initialize(self, level: float = 0.98):
        data = self._init_data
        level = level - np.floor(level)

        _data = sorted(data)
        # t is fixed for the whole algorithm
        init_thresholds = {
            "upper": _data[int(level * data.size)],
            "lower": _data[int((1 - level) * data.size)],
        }
        for key, ev in self._ev.items():
            ev.initialize(data=data, init_threshold=init_thresholds[key])
        self._num = data.size

    def run(self, with_alarm: bool = True) -> dict:
        """
        Run biSPOT on the stream

        Parameters:
            with_alarm: If False, SPOT will adapt the threshold assuming
                there is no abnormal values (default = True)

        Returns:
            a dict:
                keys : 'upper_thresholds', 'lower_thresholds' and 'alarms'

                '*_thresholds' contains the extreme quantiles and 'alarms' contains
                the indexes of the values which have triggered alarms

        """
        if self._num > self._init_data.size:
            self._logger.warning(
                "the algorithm seems to have already been run, "
                "you should initialize before running again"
            )
            return {}

        # list of the thresholds
        thresholds = {key: [] for key in self._ev}
        alarms = []
        # Loop over the stream
        for i, datum in enumerate(self._data):
            ret = {
                ev.run(datum, self._num, with_alarm=with_alarm)
                for ev in self._ev.values()
            }
            if ExtremeValue.Status.ALARM in ret:
                alarms.append(i)
            else:
                self._num += 1
            for key, ev in self._ev.items():
                thresholds[key].append(ev.extreme_quantile)

        return {
            "upper_thresholds": thresholds["upper"],
            "lower_thresholds": thresholds["lower"],
            "alarms": alarms,
        }
