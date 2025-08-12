import pathlib

from experiment_controller.rca_evaluator import RCAEvaluator
from rca_methods.rca_factory import RCAMethodEnum

current_path = pathlib.Path(__file__).parent

RCA_METHODS_TO_EVALUATE = [RCAMethodEnum.BARO, RCAMethodEnum.CAUSALAI]

rca_evaluator = RCAEvaluator(
    current_path / "example_experiment",
    RCA_METHODS_TO_EVALUATE,
)

rca_evaluator.create_report()
