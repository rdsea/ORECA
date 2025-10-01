#!/bin/bash
set -euo pipefail

uninstall_helm_releases() {
  local context="$1"
  shift
  local namespace="$1"
  shift
  local releases=("$@")

  echo "Switching to context: $context"
  kubectl config use-context "$context"

  for release in "${releases[@]}"; do
    echo "Uninstalling Helm release: $release (namespace: $namespace)"
    helm uninstall -n "$namespace" "$release" || true

    echo "Waiting for resources of $release to be deleted..."
    while true; do
      resources=$(kubectl get all -n "$namespace" -l "app.kubernetes.io/instance=$release" --ignore-not-found)
      if [[ -z "$resources" ]]; then
        echo "✅ $release fully deleted."
        break
      else
        echo "⏳ $release still terminating..."
        sleep 5
      fi
    done
  done
}

# Clean up
# Cloud part
uninstall_helm_releases cloud observe prometheus jaeger my-opentelemetry-collector blackbox-exporter
kubectl delete -n observe pvc prometheus-prometheus-kube-prometheus-prometheus-db-prometheus-prometheus-kube-prometheus-prometheus-0 --ignore-not-found
kubectl delete -n observe pvc data-jaeger-elasticsearch-master-0 --ignore-not-found
kubectl delete -n observe pvc data-jaeger-elasticsearch-data-0 --ignore-not-found

# Edge part
uninstall_helm_releases edge observe prometheus my-opentelemetry-collector blackbox-exporter
kubectl delete -n observe pvc prometheus-prometheus-kube-prometheus-prometheus-db-prometheus-prometheus-kube-prometheus-prometheus-0 --ignore-not-found

# Redeploy
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELM_PATH=$SCRIPT_DIR/../../helm_charts

# Cloud part
kubectl config use-context cloud
kubectl create namespace dashboard || true
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n observe --values "$HELM_PATH/prometheus/values_cloud.yaml" --create-namespace --version 75.12.0

helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter \
  -n observe --values "$HELM_PATH/prometheus/blackbox_exporter.yaml" --version 11.3.1

kubectl wait --namespace=observe --for=condition=Ready pod --all --timeout=300s

helm install jaeger jaegertracing/jaeger \
  -n observe --create-namespace -f "$HELM_PATH/jaeger/values.yaml" --version 3.4.1
kubectl wait --namespace=observe --for=condition=Ready pod --all --timeout=300s

helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector \
  -f "$HELM_PATH/otel/values_cloud.yaml" -n observe --version 0.129.0
kubectl wait --namespace=observe --for=condition=Ready pod --all --timeout=300s

# Edge part
kubectl config use-context edge
helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector \
  -f "$HELM_PATH/otel/values_edge.yaml" -n observe --version 0.129.0

kubectl create namespace dashboard || true
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n observe --values "$HELM_PATH/prometheus/values_edge.yaml" --create-namespace --version 75.12.0

helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter \
  -n observe --values "$HELM_PATH/prometheus/blackbox_exporter.yaml" --version 11.3.1

kubectl wait --namespace=observe --for=condition=Ready pod --all --timeout=300s
