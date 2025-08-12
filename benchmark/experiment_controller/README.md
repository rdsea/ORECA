# Experiment Controller

This directory contains the experiment controller component of the RCA benchmarking framework. It is used to:

1. Introduce various types of faults into the system to test the resilience and performance of applications
2. Collect telemetry data during fault injection
3. Evaluate the effectiveness of RCA (Root Cause Analysis) methods using the collected data

## Features

The experiment controller supports multiple fault types:
- Network faults: DELAY, LOSS
- Resource faults: CPU, MEMORY

## RCA Evaluation

The RCA evaluator can compare different RCA methods against collected telemetry data. Results are now displayed in a table format organized by fault type:

| Fault Type | Precision@1 | Recall@1 | Accuracy@1 | Precision@3 | Recall@3 | Accuracy@3 | Precision@5 | Recall@5 | Accuracy@5 | MRR |
|------------|-------------|----------|------------|-------------|----------|------------|-------------|----------|------------|-----|
| NetworkFault.DELAY | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Usage

To run an RCA evaluation:
```python
from experiment_controller.rca_evaluator import RCAEvaluator
from rca_methods.rca_factory import RCAMethodEnum

# Specify which RCA methods to evaluate
RCA_METHODS_TO_EVALUATE = [RCAMethodEnum.BARO]

# Create evaluator instance
rca_evaluator = RCAEvaluator(
    Path("path/to/experiment/data"),
    RCA_METHODS_TO_EVALUATE,
)

# Generate and display results in table format
rca_evaluator.create_report()
```

Note: For meaningful results, ensure that the `ground_truth` field in your experiment configuration files is set to actual root cause identifiers, not placeholder values.