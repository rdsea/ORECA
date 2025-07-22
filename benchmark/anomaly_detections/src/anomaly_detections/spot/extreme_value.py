import logging
from collections.abc import Callable
from enum import Enum, auto
from typing import TypeVar

import numpy as np
from scipy.optimize import minimize

from anomaly_detections.spot.utils import asc_key

_Template = TypeVar("_Template")


class ExtremeValue:
    """
    Extreme value with one threshold
    """

    class Status(Enum):
        """
        Detection result
        """

        NORMAL = auto()
        ABNORMAL = auto()
        ALARM = auto()

    def __init__(
        self,
        q: float = 1e-4,
        n_points: int = 10,
        key: Callable[[_Template], _Template] = asc_key,
        logging_level: int = logging.WARNING,
    ):
        """
        Constructor

        Parameters:
            q: Detection level (risk)
            n_points: maximum number of candidates for maximum likelihood (default : 10)
        """
        self._proba = q
        self._n_points = n_points
        self._key = key

        self._extreme_quantile: float | None = None
        self._init_threshold: float | None = None
        self._peaks: np.ndarray | None = None

        self._logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )
        self._logger.setLevel(level=logging_level)

    @property
    def extreme_quantile(self) -> float:
        """
        current threshold (bound between normal and abnormal events)
        """
        return self._extreme_quantile

    @property
    def num_peaks(self) -> int:
        """
        number of observed peaks
        """
        return self._peaks.size

    def summary(self) -> dict:
        """
        Summary running status
        """
        return {
            "Detection level q": self._proba,
            "initial threshold": self._init_threshold,
            "#(peaks)": self.num_peaks,
            "extreme quantile": self._extreme_quantile,
        }

    @staticmethod
    def _roots_finder(
        fun: Callable[[float], float],
        jac: Callable[[float], float],
        bounds: tuple[float, float],
        npoints: int,
        method: str,
    ) -> np.ndarray:
        """
        Find possible roots of a scalar function

        Parameters:
            fun: scalar function
            jac: first order derivative of the function
            bounds: (min,max) interval for the roots search
            npoints: maximum number of roots to output
            method:
                'regular' : regular sample of the search interval,
                'random' : uniform (distribution) sample of the search interval

        Returns: possible roots of the function
        """
        if method == "regular":
            step = (bounds[1] - bounds[0]) / (npoints + 1)
            initial_guess = np.arange(bounds[0] + step, bounds[1], step)
        elif method == "random":
            initial_guess = np.random.uniform(bounds[0], bounds[1], npoints)

        def _object(variable: np.ndarray) -> tuple[float, np.ndarray]:
            value = np.array([fun(item) for item in variable])
            gradient = np.array([jac(item) for item in variable])
            return (value**2).sum(), 2 * value * gradient

        opt = minimize(
            _object,
            initial_guess,
            method="L-BFGS-B",
            jac=True,
            bounds=[bounds] * len(initial_guess),
        )

        big_x: np.ndarray = opt.x
        np.round(big_x, decimals=5)
        return np.unique(big_x)

    @staticmethod
    def _log_likelihood(big_y: np.ndarray, gamma: float, sigma: float) -> float:
        """
        Compute the log-likelihood for the Generalized Pareto Distribution (μ=0)

        Parameters:
            Y: observations
            gamma: GPD index parameter
            sigma: GPD scale parameter (>0)

        Returns: log-likelihood of the sample Y to be drawn from a GPD(gamma,sigma,mu=0)
        """
        n = big_y.size
        if gamma != 0:
            tau = gamma / sigma
            big_l = (
                -n * np.log(sigma) - (1 + (1 / gamma)) * (np.log(1 + tau * big_y)).sum()
            )
        else:
            big_l = n * (1 + np.log(big_y.mean()))
        return big_l

    def _grimshaw(
        self, peaks: np.ndarray, epsilon: float = 1e-8
    ) -> tuple[float, float, float]:
        # pylint: disable=too-many-locals
        """
        Compute the GPD parameters estimation with the Grimshaw's trick

        Parameters:
            epsilon: numerical parameter to perform (default : 1e-8)

        Returns: gamma estimates, sigma estimates and corresponding log-likelihood
        """

        def _u(s: np.ndarray) -> float:
            return 1 + np.log(s).mean()

        def _v(s: np.ndarray) -> float:
            return np.mean(1 / s)

        def _w(t: float) -> float:
            s = 1 + t * peaks
            us = _u(s)
            vs = _v(s)
            return us * vs - 1

        def _jac_w(t: float) -> float:
            s = 1 + t * peaks
            us = _u(s)
            vs = _v(s)
            jac_us = (1 / t) * (1 - vs)
            jac_vs = (1 / t) * (-vs + np.mean(1 / s**2))
            return us * jac_vs + vs * jac_us

        y_min: float = peaks.min()
        y_max: float = peaks.max()
        y_mean: float = peaks.mean()

        a = -1 / y_max
        if abs(a) < 3 * epsilon:
            epsilon = abs(a) / self._n_points

        a = a + epsilon

        # We look for possible roots
        left_zeros = self._roots_finder(
            _w,
            _jac_w,
            (a + epsilon, -epsilon),
            self._n_points,
            "regular",
        )

        if y_mean > y_min > 0 and not np.isclose(y_mean, y_min):
            b = 2 * (y_mean - y_min) / (y_mean * y_min)
            c = 2 * (y_mean - y_min) / (y_min**2)
            right_zeros = self._roots_finder(
                _w,
                _jac_w,
                (b, c),
                self._n_points,
                "regular",
            )
            # all the possible roots
            zeros = np.concatenate((left_zeros, right_zeros))
        else:
            zeros = left_zeros

        # 0 is always a solution so we initialize with it
        gamma_best = 0
        sigma_best = y_mean
        ll_best = self._log_likelihood(peaks, gamma_best, sigma_best)

        # we look for better candidates
        for z in zeros:
            gamma = _u(1 + z * peaks) - 1
            sigma = gamma / z
            ll = self._log_likelihood(peaks, gamma, sigma)
            if ll > ll_best:
                gamma_best = gamma
                sigma_best = sigma
                ll_best = ll

        return gamma_best, sigma_best, ll_best

    def _quantile(self, num: int, gamma: float, sigma: float) -> float:
        """
        Compute the quantile at level 1-q

        Parameters:
            gamma: GPD parameter
            sigma: GPD parameter

        Returns: quantile at level 1-q for the GPD(gamma,sigma,mu=0)
        """
        r = num * self._proba / self.num_peaks
        if gamma != 0:
            return self._init_threshold + self._key(
                (sigma / gamma) * (pow(r, -gamma) - 1)
            )
        return self._init_threshold - self._key(sigma * np.log(r))

    def initialize(self, data: np.ndarray, init_threshold: float):
        """
        Run the calibration (initialization) step
        """
        self._init_threshold = init_threshold

        # initial peaks
        self._peaks = self._key(
            data[self._key(data) > self._key(self._init_threshold)]
            - self._init_threshold
        )

        self._logger.debug("Initial threshold : %s", self._init_threshold)
        self._logger.debug("Number of peaks : %s", self.num_peaks)
        self._logger.debug("Grimshaw maximum log-likelihood estimation ... ")

        if self._peaks.size:
            gamma, sigma, ll = self._grimshaw(self._peaks)
            self._extreme_quantile = self._quantile(data.size, gamma, sigma)
            self._logger.debug(
                "gamma = %s, sigma = %s, log-likelihood = %s", gamma, sigma, ll
            )
        else:
            self._extreme_quantile = self._init_threshold
            self._logger.info("Initialized with no peaks")
        self._logger.debug(
            "Extreme quantile (probability = %s): %s",
            self._proba,
            self._extreme_quantile,
        )

    def run(self, datum: float, num: int, with_alarm: bool = True) -> Status:
        """
        Run SPOT on the stream

        Parameters:
            with_alarm: If False, SPOT will adapt the threshold assuming
                there is no abnormal values (default = True)
        """
        # If the observed value exceeds the current threshold (alarm case)
        if self._key(datum) > self._key(self._extreme_quantile):
            # if we want to alarm, we put it in the alarm list
            if with_alarm:
                return self.Status.ALARM
            # otherwise we add it in the peaks
            self._peaks = np.append(
                self._peaks, self._key(datum - self._init_threshold)
            )
            # and we update the thresholds

            g, s, _ = self._grimshaw(self._peaks)
            self._extreme_quantile = self._quantile(num + 1, g, s)

        # case where the value exceeds the initial threshold but not the alarm ones
        elif self._key(datum) > self._key(self._init_threshold):
            # we add it in the peaks
            self._peaks = np.append(
                self._peaks, self._key(datum - self._init_threshold)
            )
            # and we update the thresholds

            g, s, _ = self._grimshaw(self._peaks)
            self._extreme_quantile = self._quantile(num + 1, g, s)
        else:
            return self.Status.NORMAL
        return self.Status.ABNORMAL
