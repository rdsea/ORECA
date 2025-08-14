#!/bin/bash

set -e

# Cilium
# helm repo add cilium https://helm.cilium.io/
# helm install cilium cilium/cilium --version 1.17.5 \
#   --namespace kube-system --values cilium_values.yaml
# kubectl wait --namespace kube-system --for=condition=Available deploy --all --timeout=300s

# Prometheus
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
kubectl create namespace dashboard || true
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n observe --values values.yaml --create-namespace --version 75.12.0

# Longhorn
helm repo add longhorn https://charts.longhorn.io
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace --version 1.9.0 --values values.yaml
kubectl wait --namespace longhorn-system --for=condition=Available deploy --all --timeout=300s
kubectl wait --namespace longhorn-system --for=condition=Ready pod --all --timeout=300s

# Jaeger
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  -n observe --create-namespace -f values.yaml --version 3.4.1
kubectl wait --namespace observe --for=condition=Available deploy --all --timeout=300s

# Otel collector
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector \
  -f values.yaml -n observe --version 0.129.0
kubectl wait --namespace observe --for=condition=Available deploy --all --timeout=300s
