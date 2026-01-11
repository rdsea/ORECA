# ORECA Experiment Controller

The ORECA Experiment Controller is the core component responsible for managing experimental workflows, fault injection, and evaluation of Root Cause Analysis (RCA) methods in distributed systems.

## Supported Fault Types

The experiment controller supports multiple fault categories:

- **Network faults**: DELAY, LOSS
- **Resource faults**: CPU, MEMORY

## Evaluation Metrics

The framework evaluates RCA methods using standardized metrics:

| Metric      | Description                                            |
| ----------- | ------------------------------------------------------ |
| Precision@k | Fraction of retrieved causes that are relevant (top-k) |
| Recall@k    | Fraction of relevant causes that are retrieved (top-k) |
| Accuracy@k  | Fraction of correct predictions among top-k candidates |
| MRR         | Mean Reciprocal Rank of the first correct prediction   |

## Usage

### Basic RCA Evaluation

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

### Experiment Configuration

Configure experiments using JSON/YAML configuration files that specify:

- Target applications and services
- Fault injection parameters
- Evaluation criteria and ground truth
- Infrastructure connection details

## Experiment Scripts

Predefined experiment scripts are available in the `docs/ml_serving/` directory:

- `experiment_cadence.py`: Evaluates RCA performance under different fault cadences
- `experiment_elasticity.py`: Tests system elasticity under various conditions
- `experiment_severity.py`: Assesses RCA effectiveness with varying fault severity
- `example_rca_evaluator.py`: Demonstrates how to run custom evaluations

## Directory Structure

```
experiment_controller/
├── docs/
│   ├── ml_serving/          # ML serving experiment scripts
│   └── train_ticket/        # Train ticket system experiments
├── src/                     # Source code
├── tests/                   # Unit and integration tests
└── README.md                # This file
```

