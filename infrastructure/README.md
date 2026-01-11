# Infrastructure Setup Guide

This guide describes how to set up the edge-cloud infrastructure required for running ORECA experiments.

## Edge Cluster Setup

### Prerequisites
- Multiple Jetson devices (minimum 4 recommended: 1 control-plane + 3 workers)
- Network connectivity between devices
- SSH access to all devices

### Creating k3s cluster

1. Install k3s on each device using k3sup or manual installation
2. Configure the cluster with the following specifications:
   - 1 control-plane node
   - 3 worker nodes
   - Proper networking configuration

### Deploy necessary tools

Deploy the following components to enable full functionality:

1. **Metric-server**: For Kubernetes metrics
2. **Gateway-api**: For API gateway functionality
3. **Cilium**: As Container Network Interface (CNI)
4. **Prometheus**: For metrics collection
5. **Longhorn**: For storage management

## Cloud Cluster Setup

### Options

Choose one of the following approaches:

#### Real cloud using Terraform
- Use provided Terraform configurations to provision KVM instances with Talos OS
- Follow the specifications outlined in the experiment documentation

#### Local cloud using k3s
- Similar setup to edge cluster but on cloud infrastructure
- Ensure compatibility with edge cluster configuration

### Required Components
Both cloud and edge clusters require the same core components listed above.

## Connecting Edge and Cloud

### Cilium Cluster Mesh
Connect the edge and cloud clusters using Cilium clustermesh following the official guide:
- Follow the [Cilium clustermesh guide](https://docs.cilium.io/en/stable/network/clustermesh/clustermesh/)
- Ensure proper cross-cluster connectivity and routing

## Automation Scripts

The following scripts are provided to simplify infrastructure setup:
- `install_cloud.sh`: Automated cloud cluster setup
- `install_edge.sh`: Automated edge cluster setup

## Verification

After setup, verify that:
- Both clusters are operational
- Cross-cluster connectivity is established
- All required tools are deployed and functional
- Network policies allow communication between clusters as needed
