# ORECA Benchmark Suite

The ORECA benchmark suite provides tools for managing experiments, controlling telemetry stacks, and evaluating Root Cause Analysis (RCA) methods in distributed systems.

## Overview

The benchmark suite includes:

- **Experiment Controller**: Manages experimental workflows and fault injection
- **RCA Methods**: Collection of baseline RCA algorithms for comparison
- **CLI Tools**: Command-line interface for managing the experimental environment
- **Telemetry Stack**: Comprehensive monitoring and data collection infrastructure

## Quick Start

### Environment Setup

1. Create a virtual environment using [uv](https://docs.astral.sh/uv/) (recommended):

   ```bash
   uv sync
   ```

   Or create your own virtual environment and install dependencies:

   ```bash
   pip install -r uv.lock
   ```

2. Run the CLI:
   ```bash
   python3 cli.py
   ```

## CLI Commands

| Command                 | Description                         |
| ----------------------- | ----------------------------------- |
| `init_telemetry`        | Initialize the full telemetry stack |
| `destroy`               | Destroy the entire telemetry stack  |
| `init_metric`           | Start the metrics service           |
| `destroy_metric`        | Stop the metrics service            |
| `init_log`              | Start the logging service           |
| `destroy_log`           | Stop the logging service            |
| `init_visualization`    | Start visualization components      |
| `destroy_visualization` | Stop visualization components       |
| `set_log_level`         | Change logging verbosity            |
| `exit`                  | Exit the CLI                        |

## Components

### Experiment Controller

Located in `experiment_controller/`, this component manages:

- Fault injection scenarios
- Data collection during experiments
- Evaluation of RCA methods

### RCA Methods

Located in `rca_methods/`, this directory contains various baseline RCA algorithms that can be evaluated using the framework.

### Deployments

Contains Kubernetes deployment configurations for the experimental environment.

## Usage Examples

For detailed usage examples, refer to the experiment scripts in `experiment_controller/docs/ml_serving/`:

- `experiment_cadence.py`: Evaluates RCA performance under different fault cadences
- `experiment_elasticity.py`: Tests system elasticity under various conditions
- `experiment_severity.py`: Assesses RCA effectiveness with varying fault severity

## Configuration

The benchmark suite uses configuration files to specify:

- Target applications for experiments
- Fault injection parameters
- Evaluation metrics and thresholds
- Infrastructure connection details
