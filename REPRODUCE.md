# Reproducing ORECA Experimental Results

This document provides detailed instructions for reproducing the experimental results presented in the ORECA thesis. Following these steps will allow you to replicate the experiments and validate the findings.

## Repository Information

- **Repository**: https://github.com/rdsea/ORECA
- **Thesis Snapshot Tag**: `master-thesis`
- **License**: Apache 2.0

## Hardware Requirements

To reproduce the experiments accurately, you should use hardware similar to the specifications described in the thesis:

### Cloud Cluster

- KVM instances with Talos OS
- Specifications as detailed in the thesis

### Edge Cluster

- 4 Jetson devices (1 control-plane + 3 worker nodes)
- k3s cluster configuration

## Infrastructure Setup

### 1. Cloud Cluster Setup

1. **Provision KVM instances** with Talos OS according to the specifications in the thesis
2. **Deploy required tools**:
   - Cilium CNI
   - Cilium cluster mesh
   - Longhorn
   - Chaos-mesh

### 2. Edge Cluster Setup

1. **Provision k3s cluster** with 1 control-plane and 3 worker nodes on top of 4 Jetson devices
2. **Deploy required tools**:
   - Cilium CNI
   - Cilium cluster mesh
   - Longhorn
   - Chaos-mesh

### 3. Connect Edge and Cloud

- Establish connectivity between edge and cloud clusters using Cilium cluster mesh
- Verify cross-cluster communication

## Host Setup for ORECA

Set up the host machine where ORECA will run:

1. **Configure cluster credentials**:
   - Ensure credentials for edge and cloud clusters are correctly specified
   - Verify that credentials can be used by ORECA

2. **Configure workload generator credentials**:
   - Set up credentials for machines used to generate workload

3. **Verify connectivity**:
   - Ensure connectivity from the host to edge/cloud clusters
   - Verify connectivity to workload generator machines

4. **Install dependencies**:
   - Set up virtual environment with required dependencies
   - Install ORECA and its dependencies

## Running Experiments

### 1. Navigate to Experiment Scripts

The experiment scripts are located in `benchmark/experiment_controller/docs/ml_serving/`:

- `experiment_cadence.py`: Evaluates RCA performance under different fault cadences
- `experiment_elasticity.py`: Tests system elasticity under various conditions
- `experiment_severity.py`: Assesses RCA effectiveness with varying fault severity

### 2. Execute Experiments

Run individual experiments using Python:

```bash
cd benchmark/experiment_controller/docs/ml_serving/
python3 experiment_elasticity.py
```

### 3. Run RCA Evaluation

Using the example RCA evaluator provided in `benchmark/experiment_controller/docs/ml_serving/example_rca_evaluator.py`:

1. Define the path to the evaluation dataset
2. Select the baseline RCA algorithms to evaluate
3. Execute the script:

```bash
python3 example_rca_evaluator.py
```

## Expected Results

The evaluation will produce results in a table format showing metrics such as:

- Precision@1, Precision@3, Precision@5
- Recall@1, Recall@3, Recall@5
- Accuracy@1, Accuracy@3, Accuracy@5
- Mean Reciprocal Rank (MRR)

## Customization

### Adding New RCA Methods

New RCA methods can be integrated by:

1. Adding the method to the `rca_methods/` directory
2. Registering the method in the RCA factory
3. Including it in evaluation scripts

