import json
import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class SPOTBase:
    """Base class for the SPOT algorithm.

    This class provides the basic functionality for the SPOT (Streaming Peaks-Over-Threshold) algorithm, including data management and plotting.
    """

    # colors for plot
    DEEP_SAFFRON = "#FF9933"
    AIR_FORCE_BLUE = "#5D8AA8"
    # keys for the plot
    _plot_keys = ()

    def __init__(self, logging_level: int = logging.WARNING):
        """Initialize the SPOTBase class.

        Args:
            logging_level (int, optional): The logging level. Defaults to logging.WARNING.
        """
        self._data: np.ndarray = None
        self._init_data: np.ndarray = None
        self._num: int = 0

        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._logger.setLevel(level=logging_level)

    def summary(self) -> dict:
        """Get a summary of the running status."""
        report = {
            "name": "Streaming Peaks-Over-Threshold Object",
        }
        if self._data is not None:
            report["Data imported"] = "Yes"
            report["#(initialization values)"] = self._init_data.size
            report["#(stream values)"] = self._data.size
        else:
            report["Data imported"] = "No"
            return report

        if self._num == 0:
            report["Algorithm initialized"] = "No"
        else:
            report["Algorithm initialized"] = "Yes"
            rest = self._num - self._init_data.size
            if rest > 0:
                report["Algorithm run"] = "Yes"
                report["#(observations)"] = f"{rest} ({100 * rest / self._num:.2f} %%)"
            else:
                report["Algorithm run"] = "No"
        return report

    def __str__(self):
        """Get a string representation of the summary."""
        return json.dumps(self.summary(), indent=2, ensure_ascii=False)

    def fit(
        self,
        init_data: np.ndarray | pd.Series | list | int | float,
        data: np.ndarray | pd.Series | list,
    ):
        """Import data to the SPOT object.

        Args:
            init_data (np.ndarray | pd.Series | list | int | float): The initial batch of data to calibrate the algorithm.
            data (np.ndarray | pd.Series | list): The data for the run.
        """
        if isinstance(data, list):
            self._data = np.array(data)
        elif isinstance(data, np.ndarray):
            self._data = data
        elif isinstance(data, pd.Series):
            self._data = data.values
        else:
            self._logger.warning("This data format (%s) is not supported", type(data))
            return

        if isinstance(init_data, list):
            self._init_data = np.array(init_data)
        elif isinstance(init_data, np.ndarray):
            self._init_data = init_data
        elif isinstance(init_data, pd.Series):
            self._init_data = init_data.values
        elif isinstance(init_data, int):
            self._init_data = self._data[:init_data]
            self._data = self._data[init_data:]
        elif isinstance(init_data, float) and (0 < init_data < 1):
            r = int(init_data * data.size)
            self._init_data = self._data[:r]
            self._data = self._data[r:]
        else:
            self._logger.warning("The initial data cannot be set")
            return

    def add(self, data: np.ndarray | pd.Series | list):
        """Append data to the already fitted data.

        Args:
            data (np.ndarray | pd.Series | list): The data to append.
        """
        if isinstance(data, list):
            data = np.array(data)
        elif isinstance(data, pd.Series):
            data = data.values
        elif not isinstance(data, np.ndarray):
            self._logger.warning("This data format (%s) is not supported", type(data))
            return

        self._data = np.append(self._data, data)

    def initialize(self, level: float = 0.98):
        """Run the calibration (initialization) step.

        Args:
            level (float, optional): The probability associated with the initial threshold t. Defaults to 0.98.
        """
        raise NotImplementedError

    def run(self, with_alarm: bool = True) -> dict:
        """Run SPOT on the stream.

        Args:
            with_alarm (bool, optional): If False, SPOT will adapt the threshold assuming there is no abnormal values. Defaults to True.

        Returns:
            dict: A dictionary containing the results of the run.
        """
        raise NotImplementedError

    def plot(self, run_results: dict, with_alarm: bool = True):
        """Plot the results of the run.

        Args:
            run_results (dict): The results given by the 'run' method.
            with_alarm (bool, optional): If True, alarms are plotted. Defaults to True.

        Returns:
            list: A list of the plots.
        """
        ticks = list(range(self._data.size))

        (ts_fig,) = plt.plot(ticks, self._data, color=self.AIR_FORCE_BLUE)
        fig = [ts_fig]

        for key in self._plot_keys:
            if key in run_results:
                (sub_fig,) = plt.plot(
                    ticks, run_results[key], color=self.DEEP_SAFFRON, lw=2, ls="dashed"
                )
                fig.append(sub_fig)

        if with_alarm and ("alarms" in run_results):
            alarm = run_results["alarms"]
            if alarm:
                fig.append(plt.scatter(alarm, self._data[alarm], color="red"))

        plt.xlim((0, self._data.size))

        return fig
