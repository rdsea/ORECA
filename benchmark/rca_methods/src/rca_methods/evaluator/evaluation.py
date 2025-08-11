class RCAEvaluator:
    """A class for evaluating RCA (Root Cause Analysis) methods."""

    def __init__(self, k_values: list | None = None):
        """Initialize the evaluator.
        Args:
            k_values (list, optional): A list of k values for which to compute the metrics. Defaults to [1, 3, 5].
        """
        if k_values is None:
            k_values = [1, 3, 5]
        self.k_values = k_values

    def precision_at_k(self, predictions: dict, ground_truth: dict, k: int) -> float:
        """Calculate the Precision at K (Precision@k) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            ground_truth (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
            k (int): The value of k.
        Returns:
            float: The Precision@k score.
        """
        total_cases = len(predictions)
        precision_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = ground_truth.get(case_id, set())
            match_count = sum(1 for pred in pred_list if pred in gt_set)
            precision = match_count / k if k > 0 else 0.0
            precision_sum += precision

        return precision_sum / total_cases if total_cases > 0 else 0.0

    def recall_at_k(self, predictions: dict, ground_truth: dict, k: int) -> float:
        """Calculate the Recall at K (Recall@k) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            ground_truth (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
            k (int): The value of k.
        Returns:
            float: The Recall@k score.
        """
        total_cases = len(predictions)
        recall_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = ground_truth.get(case_id, set())
            match_count = sum(1 for pred in pred_list if pred in gt_set)
            recall = match_count / len(gt_set) if gt_set else 0.0
            recall_sum += recall

        return recall_sum / total_cases if total_cases > 0 else 0.0

    def accuracy_at_k(self, predictions: dict, ground_truth: dict, k: int) -> float:
        """Calculate the Accuracy at K (Accuracy@k) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            ground_truth (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
            k (int): The value of k.
        Returns:
            float: The Accuracy@k score.
        """
        total_cases = len(predictions)
        correct_predictions = 0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = ground_truth.get(case_id, set())
            if any(pred in gt_set for pred in pred_list):
                correct_predictions += 1

        return correct_predictions / total_cases if total_cases > 0 else 0.0

    def mean_reciprocal_rank(self, predictions: dict, ground_truth: dict) -> float:
        """Calculate the Mean Reciprocal Rank (MRR) metric.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            ground_truth (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
        Returns:
            float: The MRR score.
        """
        total_cases = len(predictions)
        mrr_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id]
            gt_set = ground_truth.get(case_id, set())
            for i, pred in enumerate(pred_list):
                if pred in gt_set:
                    mrr_sum += 1 / (i + 1)
                    break
        return mrr_sum / total_cases if total_cases > 0 else 0.0

    def evaluate(self, predictions: dict, ground_truth: dict) -> dict:
        """Evaluate the predictions against the ground truth.
        Args:
            predictions (dict): A dictionary of predictions, where the keys are experiment ID and the values are lists of predicted root causes.
            ground_truth (dict): A dictionary of ground truth, where the keys are experiment ID and the values are sets of actual root causes.
        Returns:
            dict: A dictionary of evaluation results, where the keys are the metric names and the values are the scores.
        """
        results = {}
        for k in self.k_values:
            results[f"precision_at_{k}"] = self.precision_at_k(
                predictions, ground_truth, k
            )
            results[f"recall_at_{k}"] = self.recall_at_k(predictions, ground_truth, k)
            results[f"accuracy_at_{k}"] = self.accuracy_at_k(
                predictions, ground_truth, k
            )
        results["mean_reciprocal_rank"] = self.mean_reciprocal_rank(
            predictions, ground_truth
        )
        return results


if __name__ == "__main__":
    predictions = {
        "case1": ["C", "B", "A"],
        "case2": ["D", "E", "F"],
        "case3": ["A", "B", "D"],
    }

    ground_truth = {"case1": {"A", "B"}, "case2": {"E"}, "case3": {"C"}}

    evaluator = RCAEvaluator()
    results = evaluator.evaluate(predictions, ground_truth)
    print(results)
