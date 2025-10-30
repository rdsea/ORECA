import pytest
from experiment_controller.rca_evaluator import RCAEvaluator
from rca_methods.rca_factory import RCAMethodEnum


@pytest.fixture
def evaluator(tmp_path):
    return RCAEvaluator(dataset_path=tmp_path, rca_methods=[RCAMethodEnum.BARO])


@pytest.fixture
def sample_data():
    predictions = {
        "exp1": ["a", "b", "c"],
        "exp2": ["x", "y", "z"],
    }
    root_cause = {
        "exp1": {"a"},
        "exp2": {"y"},
    }
    return predictions, root_cause


def test_precision_at_k(evaluator, sample_data):
    predictions, root_cause = sample_data
    assert evaluator.precision_at_k(predictions, root_cause, 1) == pytest.approx(0.5)
    assert evaluator.precision_at_k(predictions, root_cause, 2) == pytest.approx(0.5)
    assert evaluator.precision_at_k(predictions, root_cause, 3) == pytest.approx(1 / 3)


def test_recall_at_k(evaluator, sample_data):
    predictions, root_cause = sample_data
    assert evaluator.recall_at_k(predictions, root_cause, 1) == pytest.approx(0.5)
    assert evaluator.recall_at_k(predictions, root_cause, 2) == pytest.approx(1.0)
    assert evaluator.recall_at_k(predictions, root_cause, 3) == pytest.approx(1.0)


def test_accuracy_at_k(evaluator, sample_data):
    predictions, root_cause = sample_data
    assert evaluator.accuracy_at_k(predictions, root_cause, 1) == pytest.approx(0.5)
    assert evaluator.accuracy_at_k(predictions, root_cause, 2) == pytest.approx(1.0)
    assert evaluator.accuracy_at_k(predictions, root_cause, 3) == pytest.approx(1.0)


def test_mean_reciprocal_rank(evaluator, sample_data):
    predictions, root_cause = sample_data
    # exp1 match at rank 1 → 1/1 = 1.0
    # exp2 match at rank 2 → 1/2 = 0.5
    assert evaluator.mean_reciprocal_rank(predictions, root_cause) == pytest.approx(
        (1 + 0.5) / 2
    )


def test_evaluate_combined(evaluator, sample_data):
    predictions, root_cause = sample_data
    results = evaluator.evaluate(predictions, root_cause)
    expected_keys = {
        "precision_at_1",
        "recall_at_1",
        "accuracy_at_1",
        "precision_at_3",
        "recall_at_3",
        "accuracy_at_3",
        "precision_at_5",
        "recall_at_5",
        "accuracy_at_5",
        "mean_reciprocal_rank",
    }
    assert set(results.keys()) == expected_keys
    assert all(0 <= v <= 1 for v in results.values())
