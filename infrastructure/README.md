# Deploying infrastructure

## Edge

### Creating k3s cluster

- Follow our private repo EdgeDeviceManagement to use k3sup to create the cluster

### Deploy necessary tool

1. Metric-server
2. Gateway-api
3. Cilium - cni
4. Prometheus
5. Longhorn

## Cloud

### Real cloud using terraform

### Local cloud using k3s

- Follow similar steps as edge

## Connect edge and cloud using Cilium clustermesh

- Follow this [guide](https://docs.cilium.io/en/stable/network/clustermesh/clustermesh/)
