import time
from abc import ABC, abstractmethod

import pandas as pd
import psutil


class BaseRCA(ABC):
    """Abstract base class for all Root Cause Analysis (RCA) methods."""

    def __init__(self, profile: bool = False):
        """Initialize the RCA method.

        Args:
            profile (bool, optional): Whether to profile the RCA method. Defaults to False.
        """
        self.profiling_results = {}
        self.profile = profile

    def run(
        self,
        dataset: pd.DataFrame,
        injection_time: int | None,
        top_k=5,
        **kwargs,
    ) -> list[tuple[str, float]]:
        """Run the RCA method on the given dataset.

        Args:
            dataset (pd.DataFrame): The input dataset containing time series data.
            injection_time (int | None): The timestamp when the fault was injected. Can be None if not applicable.
            top_k (int, optional): The number of top root causes to return. Defaults to 5.
            **kwargs: Additional keyword arguments specific to the RCA method.

        Returns:
            list[tuple[str, float]]: A list of tuples, where each tuple contains
                                     the name of a potential root cause (str) and its score (float),
                                     sorted in descending order of score.
        """
        if self.profile:
            return self._profiled_run(dataset, injection_time, top_k, **kwargs)
        else:
            return self._run(dataset, injection_time, top_k, **kwargs)

    def _profiled_run(
        self,
        dataset: pd.DataFrame,
        injection_time: int | None,
        top_k=5,
        **kwargs,
    ) -> list[tuple[str, float]]:
        process = psutil.Process()

        # Record start time and resource usage
        start_time = time.time()
        start_cpu = process.cpu_times()
        start_mem = process.memory_info()

        # Execute the decorated function
        result = self._run(dataset, injection_time, top_k, **kwargs)

        # Record end time and resource usage
        end_time = time.time()
        end_cpu = process.cpu_times()
        end_mem = process.memory_info()

        # Calculate execution time and resource consumption
        execution_time = end_time - start_time
        cpu_usage = {
            "user": end_cpu.user - start_cpu.user,
            "system": end_cpu.system - start_cpu.system,
        }
        memory_usage = {
            "rss": end_mem.rss - start_mem.rss,  # Resident Set Size
            "vms": end_mem.vms - start_mem.vms,  # Virtual Memory Size
        }

        # Store the profiling results
        self.profiling_results = {
            "execution_time": execution_time,
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
        }

        return result

    @abstractmethod
    def _run(
        self,
        dataset: pd.DataFrame,
        injection_time: int | None,
        top_k=5,
        **kwargs,
    ) -> list[tuple[str, float]]:
        """Run the RCA method on the given dataset.

        This method should be implemented by subclasses.

        Args:
            dataset (pd.DataFrame): The input dataset containing time series data.
            injection_time (int | None): The timestamp when the fault was injected. Can be None if not applicable.
            top_k (int, optional): The number of top root causes to return. Defaults to 5.
            **kwargs: Additional keyword arguments specific to the RCA method.

        Returns:
            list[tuple[str, float]]: A list of tuples, where each tuple contains
                                     the name of a potential root cause (str) and its score (float),
                                     sorted in descending order of score.
        """
        pass
