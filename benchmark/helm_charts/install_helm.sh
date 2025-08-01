#!/bin/bash

# Cilium
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --version 1.17.5 \
  --namespace kube-system --values cilium_values.yaml

# Prometheus
# Create namespace for grafana dashboard as this's not automatically done by helm
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
kubectl create namespace dashboard
helm install prometheus prometheus-community/kube-prometheus-stack -n observe --values values.yaml --create-namespace

# Longhorn
# Install requirement before deploying longhorn to all node https://longhorn.io/docs/1.9.0/deploy/install/#installing-open-iscsi
helm repo add longhorn https://charts.longhorn.io
helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.9.0 --values values.yaml

# Jaeger
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger -n observe --create-namespace -f values.yaml

# Otel collector
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector \
  -f values.yaml -n observe
