"""RCA Evaluator module for the experiment controller."""

import os
from pathlib import Path

import pandas as pd
from rca_methods.rca_factory import RCAFactory, RCAMethodEnum


class RCAEvaluator:
    """Evaluator for comparing different RCA methods against telemetry data."""

    def __init__(self, dataset_path: Path, rca_methods: list[RCAMethodEnum]):
        """Initialize the RCA evaluator with a path to telemetry data.

        Args:
            dataset_path (Path): Path to the directory containing telemetry data.
        """
        self.dataset_path = dataset_path
        self.rca_methods = rca_methods

    def create_report(self):
        for dir in os.listdir(self.dataset_path):
            self.process_experiment(self.dataset_path / dir)

    def process_experiment(self, experiment_dir: Path):
        for run_number in os.listdir(experiment_dir):
            self.process_data(experiment_dir / run_number)

    def process_data(self, data_dir: Path):
        data = self.load_data(data_dir / "metric.csv")
        for rca_method in self.rca_methods:
            self.evaluate_rca(rca_method, data)

    def load_data(self, data_path: Path) -> pd.DataFrame:
        return pd.DataFrame()

    def evaluate_rca(self, rca_method: RCAMethodEnum, data: pd.DataFrame):
        rca = RCAFactory.create(rca_method)
        rca.run(data, injection_time=None, top_k=5)
        pass
