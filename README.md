# ORECA - Open Framework for Root Cause Analysis Evaluation

ORECA (Open Framework for Root Cause Analysis Evaluation) is a comprehensive framework designed to systematically evaluate Root Cause Analysis (RCA) methods, particularly in edge-cloud environments. The framework enables researchers and practitioners to benchmark different RCA algorithms against standardized datasets and experimental conditions.

### Components

- **applications**: Target applications used in experiments (e.g., object classification)
- **benchmark**: Core components including experiment controller, baseline RCA algorithms, and CLI utilities
- **infrastructure**: Utilities and scripts to set up edge and cloud infrastructure
- **results**: Experimental results and evaluation data

## Key Features

- **Multi-dimensional Evaluation**: Assess RCA methods across precision, recall, accuracy, and Mean Reciprocal Rank (MRR)
- **Fault Injection**: Support for various fault types including network delays, packet loss, and resource constraints
- **Modular Architecture**: Easy integration of new RCA methods and experimental scenarios
- **Comprehensive Telemetry**: Collection of metrics, logs, and traces for analysis

## Reproducibility

The experiment results for my master thesis and the corresponding paper can be reproduced by following the detailed instructions in the [documentation](REPRODUCE.md)

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.
