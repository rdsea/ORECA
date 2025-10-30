import logging
import os
from enum import Enum
from pathlib import Path

import pandas as pd
import yaml
from rca_methods.rca_factory import RCAFactory, RCAMethodEnum
from rca_methods.utility import read_data
from tabulate import tabulate
from tqdm import tqdm

from experiment_controller.config.experiment_config import RCAExperimentConfig
from experiment_controller.experiment_controller import parse_time_to_seconds
from experiment_controller.logger import logger


class EvaluationMode(Enum):
    COARSE = "coarse-grained"
    FINE = "fine-grained"


class RCAEvaluator:
    """Evaluator for comparing different RCA methods against telemetry data.

    The RCA evaluator processes experiment data and evaluates the performance of
    different RCA methods using standard information retrieval metrics.

    Results are organized by fault type and displayed in a table format for easy comparison.

    Example:
        >>> from rca_methods.rca_factory import (
        ...     RCAMethodEnum,
        ... )
        >>> evaluator = RCAEvaluator(
        ...     dataset_path=Path(
        ...         "path/to/experiments"
        ...     ),
        ...     rca_methods=[
        ...         RCAMethodEnum.BARO
        ...     ],
        ... )
        >>> evaluator.create_report()

        # RCA Evaluation Results for BARO
        | Fault Type | Precision@1 | Recall@1 | Accuracy@1 | Precision@3 | Recall@3 | Accuracy@3 | Precision@5 | Recall@5 | Accuracy@5 | MRR |
        |------------|-------------|----------|------------|-------------|----------|------------|-------------|----------|------------|-----|
        | NetworkFault.DELAY | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
    """

    def __init__(
        self,
        dataset_path: Path,
        rca_methods: list[RCAMethodEnum],
        k_values: list[int] | None = None,
        verbose: bool = False,
    ):
        """Initialize the RCA evaluator with a path to telemetry data.

        Args:
            dataset_path (Path): Path to the directory containing experiment data.
                The directory should contain subdirectories for each experiment,
                with each experiment directory containing:
                - experiment_config.yaml: Configuration file for the experiment
                - Run directories (1, 2, 3, etc.): Each containing metric.csv files
            rca_methods (list[RCAMethodEnum]): List of RCA methods to evaluate
            k_values (list[int], optional): K values for Precision@K, Recall@K, and Accuracy@K.
                Defaults to [1, 3, 5].
            verbose (bool): Whether to enable verbose logging. Defaults to False.
        """
        self.dataset_path = dataset_path
        self.rca_methods = rca_methods
        self.predictions = {}
        self.root_cause = {}
        self.experiment_fault_types = {}  # Track fault type for each experiment
        self.verbose = verbose

        if self.verbose:
            logger.setLevel(logging.INFO)

        if k_values is None:
            k_values = [1, 3, 5]
        self.k_values = k_values

    def create_report(self):
        """Process all experiments in the dataset and generate evaluation reports.

        This method:
        1. Processes all experiment directories in the dataset path
        2. For each experiment, runs the configured RCA methods on the telemetry data
        3. Evaluates the results using multiple metrics
        4. Displays the results in a table format organized by fault type

        The results table includes:
        - Precision@K: Proportion of top-K predictions that are correct
        - Recall@K: Proportion of actual root causes identified in top-K predictions
        - Accuracy@K: Proportion of cases where at least one correct root cause is in top-K predictions
        - MRR (Mean Reciprocal Rank): Average of reciprocal ranks of first correct prediction

        Note:
            For meaningful results, ensure that the `root_cause` field in your
            experiment configuration files is set to actual root cause identifiers,
            not placeholder values.
        """
        experiment_dirs = [
            self.dataset_path / dir
            for dir in os.listdir(self.dataset_path)
            if os.path.isdir(self.dataset_path / dir)
        ]
        for dir in tqdm(experiment_dirs, desc="Processing experiments"):
            self.process_experiment(dir)

        # Generate and print results table
        self.print_results_table(EvaluationMode.COARSE)
        self.print_results_table(EvaluationMode.FINE)

    def print_results_table(self, mode: EvaluationMode):
        """Generate and print a table of results organized by fault type using tabulate."""
        fault_types = list(set(self.experiment_fault_types.values()))

        for rca_method in self.rca_methods:
            print(f"\n# RCA Evaluation Results for {rca_method.name} at {mode}")

            headers = [
                "Fault Type",
                "Precision@1",
                "Recall@1",
                "Accuracy@1",
                "Precision@3",
                "Recall@3",
                "Accuracy@3",
                "Precision@5",
                "Recall@5",
                "Accuracy@5",
                "MRR",
            ]

            table = []
            for fault_type in fault_types:
                filtered_predictions = {}
                filtered_root_cause = {}

                for experiment_id, fault in self.experiment_fault_types.items():
                    if fault == fault_type:
                        if (
                            rca_method.name in self.predictions
                            and experiment_id in self.predictions[rca_method.name]
                        ):
                            if mode == EvaluationMode.FINE:
                                predictions = self.predictions[rca_method.name][
                                    experiment_id
                                ]
                                if isinstance(predictions[0], tuple):
                                    filtered_predictions[experiment_id] = [
                                        x[0] for x in predictions
                                    ]
                                else:
                                    filtered_predictions[experiment_id] = predictions
                                filtered_root_cause[experiment_id] = self.root_cause[
                                    experiment_id
                                ]
                            else:
                                filtered_predictions[experiment_id] = [
                                    self.simplify_label(x[0])
                                    for x in self.predictions[rca_method.name][
                                        experiment_id
                                    ]
                                ]
                                filtered_root_cause[experiment_id] = (
                                    self.simplify_label(self.root_cause[experiment_id])
                                )

                if filtered_predictions:
                    results = self.evaluate(filtered_predictions, filtered_root_cause)
                    row = [
                        fault_type,
                        f"{results['precision_at_1']:.3f}",
                        f"{results['recall_at_1']:.3f}",
                        f"{results['accuracy_at_1']:.3f}",
                        f"{results['precision_at_3']:.3f}",
                        f"{results['recall_at_3']:.3f}",
                        f"{results['accuracy_at_3']:.3f}",
                        f"{results['precision_at_5']:.3f}",
                        f"{results['recall_at_5']:.3f}",
                        f"{results['accuracy_at_5']:.3f}",
                        f"{results['mean_reciprocal_rank']:.3f}",
                    ]
                else:
                    row = [fault_type] + ["-"] * (len(headers) - 1)

                table.append(row)

            print(tabulate(table, headers=headers, tablefmt="github"))

    def process_experiment(self, experiment_dir: Path):
        """Process a single experiment directory.

        This method:
        1. Loads the experiment configuration
        2. Processes all run directories within the experiment
        3. Stores ground truth and fault type information for result organization

        Args:
            experiment_dir (Path): Path to the experiment directory containing
                experiment_config.yaml and run directories
        """
        with open(experiment_dir / "experiment_config.yaml") as f:
            experiment_config = RCAExperimentConfig.model_validate(yaml.safe_load(f))

        run_dirs = [
            experiment_dir / run_number
            for run_number in os.listdir(experiment_dir)
            if os.path.isdir(experiment_dir / run_number)
        ]
        for run_dir in tqdm(
            run_dirs,
            desc=f"Processing runs for {experiment_config.experiment_name}",
            leave=False,
        ):
            run_number = run_dir.name
            experiment_id = f"{experiment_config.experiment_name}_{run_number}"
            self.root_cause[experiment_id] = (
                f"{experiment_config.root_cause.what}_{experiment_config.root_cause.where}"
            )

            # Store fault type for this experiment
            self.experiment_fault_types[experiment_id] = str(
                experiment_config.fault_config.fault_type
            )
            self.process_data(run_dir, experiment_config, experiment_id)

    def process_data(
        self, data_dir: Path, experiment_config: RCAExperimentConfig, experiment_id: str
    ):
        data = self.load_data(data_dir / "metric.csv")
        if data.empty:
            return
        injection_time = (
            data["timestamp"][0]
            + parse_time_to_seconds(
                experiment_config.fault_config.fault_injection_period
            )
            - parse_time_to_seconds(experiment_config.warm_up_interval)
        )

        for rca_method in tqdm(
            self.rca_methods, desc=f"Evaluating RCA methods for {experiment_id}"
        ):
            logger.info(
                f"Running RCA method {rca_method.name} for experiment {experiment_id}"
            )
            self.evaluate_rca(rca_method, data, injection_time, experiment_id)

    def load_data(self, data_path: Path) -> pd.DataFrame:
        data = read_data(data_path)
        if data.empty:
            return pd.DataFrame()
        return self.preprocess_data(data)

    def preprocess_data(self, df: pd.DataFrame):
        return df.drop(columns=df.columns[df.columns.str.contains("node|pod")])

    def evaluate_rca(
        self,
        rca_method: RCAMethodEnum,
        data: pd.DataFrame,
        injection_time: int,
        experiment_id: str,
    ):
        rca = RCAFactory.create(rca_method)
        rootcause = rca.run(data, injection_time, top_k=5)
        logger.debug(f"{rca_method} find root cause: {rootcause}")
        if rca_method.name not in self.predictions:
            self.predictions[rca_method.name] = {}
        self.predictions[rca_method.name][experiment_id] = rootcause

    def precision_at_k(self, predictions: dict, root_cause: dict, k: int) -> float:
        """Calculate the Precision at K (Precision@k) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            root_cause (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
            k (int): The value of k.
        Returns:
            float: The Precision@k score.
        """
        total_cases = len(predictions)
        precision_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = root_cause.get(case_id, set())
            match_count = sum(1 for pred in pred_list if pred in gt_set)
            precision = match_count / k if k > 0 else 0.0
            precision_sum += precision

        return precision_sum / total_cases if total_cases > 0 else 0.0

    def recall_at_k(self, predictions: dict, root_cause: dict, k: int) -> float:
        """Calculate the Recall at K (Recall@k) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            root_cause (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
            k (int): The value of k.
        Returns:
            float: The Recall@k score.
        """
        total_cases = len(predictions)
        recall_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = root_cause.get(case_id, set())
            match_count = sum(1 for pred in pred_list if pred in gt_set)
            recall = match_count / len(gt_set) if gt_set else 0.0
            recall_sum += recall

        return recall_sum / total_cases if total_cases > 0 else 0.0

    def accuracy_at_k(self, predictions: dict, root_cause: dict, k: int) -> float:
        """Calculate the Accuracy at K (Accuracy@k) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            root_cause (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
            k (int): The value of k.
        Returns:
            float: The Accuracy@k score.
        """
        total_cases = len(predictions)
        correct_predictions = 0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = root_cause.get(case_id, set())
            if any(pred in gt_set for pred in pred_list):
                correct_predictions += 1

        return correct_predictions / total_cases if total_cases > 0 else 0.0

    def mean_reciprocal_rank(self, predictions: dict, root_cause: dict) -> float:
        """Calculate the Mean Reciprocal Rank (MRR) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            root_cause (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
        Returns:
            float: The MRR score.
        """
        total_cases = len(predictions)
        mrr_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id]
            gt_set = root_cause.get(case_id, set())
            for i, pred in enumerate(pred_list):
                if pred in gt_set:
                    mrr_sum += 1 / (i + 1)
                    break
        return mrr_sum / total_cases if total_cases > 0 else 0.0

    def evaluate(self, predictions: dict, root_cause: dict) -> dict:
        """Evaluate the predictions against the ground truth.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            root_cause (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
        Returns:
            dict: A dictionary of evaluation results, where the keys are the metric names and the values are the scores.
        """
        results = {}
        for k in self.k_values:
            results[f"precision_at_{k}"] = self.precision_at_k(
                predictions, root_cause, k
            )
            results[f"recall_at_{k}"] = self.recall_at_k(predictions, root_cause, k)
            results[f"accuracy_at_{k}"] = self.accuracy_at_k(predictions, root_cause, k)
        results["mean_reciprocal_rank"] = self.mean_reciprocal_rank(
            predictions, root_cause
        )
        return results

    def simplify_label(self, label: str):
        """
        Simplify the label by removing the "what" and "where" parts.
        The metric is formatted as what_where
        """
        return label.split("_")[0]
