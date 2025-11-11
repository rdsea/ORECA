import pathlib

from experiment_controller.rca_evaluator import RCAEvaluator
from rca_methods.rca_factory import RCAMethodEnum

# Get the current directory
current_path = pathlib.Path(__file__).parent

# Specify which RCA methods to evaluate
# Available methods can be found in the rca_methods package
RCA_METHODS_TO_EVALUATE = [
    # RCAMethodEnum.BARO,
    # RCAMethodEnum.DUMMY,
    RCAMethodEnum.CAUSALAI,
    # RCAMethodEnum.CAUSALRCA,
    RCAMethodEnum.CIRCA,
    RCAMethodEnum.CLOUDRANGER,
]

# Create the RCA evaluator with the path to experiment data
rca_evaluator = RCAEvaluator(
    current_path / "scrape_1s.local",
    RCA_METHODS_TO_EVALUATE,
)

# Run the evaluation and display results in table format
# Results are organized by fault type for better analysis
rca_evaluator.create_report()
