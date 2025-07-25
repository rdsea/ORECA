class RCAEvaluator:
    def __init__(self, k_values: list | None = None):
        if k_values is None:
            k_values = [1, 3, 5]
        self.k_values = k_values

    def ac_at_k(self, predictions: dict, ground_truth: dict, k: int) -> float:
        total_cases = len(predictions)
        ac_sum = 0.0

        for case_id in predictions:
            pred_list = predictions[case_id][:k]
            gt_set = ground_truth.get(case_id, set())
            match_count = sum(1 for pred in pred_list if pred in gt_set)
            ac = match_count / min(k, len(gt_set)) if gt_set else 0.0
            ac_sum += ac

        return ac_sum / total_cases if total_cases > 0 else 0.0

    def avg_at_k(self, predictions: dict, ground_truth: dict, k: int) -> float:
        avg_sum = 0.0
        for j in range(1, k + 1):
            avg_sum += self.ac_at_k(predictions, ground_truth, j)
        return avg_sum / k

    def evaluate(self, predictions: dict, ground_truth: dict) -> dict:
        results = {}
        for k in self.k_values:
            results[f"AC@{k}"] = self.ac_at_k(predictions, ground_truth, k)
            results[f"Avg@{k}"] = self.avg_at_k(predictions, ground_truth, k)
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
