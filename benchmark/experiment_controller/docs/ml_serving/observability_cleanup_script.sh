#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELM_PATH=$SCRIPT_DIR/../../helm_charts

# ------------------------------
# Helpers
# ------------------------------

uninstall_helm_releases() {
  local context="$1"
  local namespace="$2"
  shift 2
  local releases=("$@")

  echo "Switching to context: $context"
  kubectl config use-context "$context"

  for release in "${releases[@]}"; do
    (
      echo "Uninstalling Helm release: $release (namespace: $namespace)"
      helm uninstall -n "$namespace" "$release" || true

      echo "Waiting for resources of $release to be deleted..."
      while kubectl get all -n "$namespace" -l "app.kubernetes.io/instance=$release" --ignore-not-found | grep -q .; do
        sleep 3
      done
      echo "✅ $release fully deleted."
    ) &
  done
  wait
}

delete_pvcs() {
  local namespace="$1"
  echo "Deleting PVCs in namespace: $namespace"
  kubectl get pvc -n "$namespace" -o name | xargs -n1 -P4 kubectl delete --wait --ignore-not-found || true
}

wait_for_critical_pods() {
  local namespace="$1"
  shift
  local labels=("$@")
  for label in "${labels[@]}"; do
    echo "Waiting for critical pods with label: $label"
    kubectl wait -n "$namespace" --for=condition=Ready pod -l "$label" --timeout=300s || true
  done
}

helm_install_parallel() {
  local installs=("$@")
  for cmd in "${installs[@]}"; do
    (
      eval "$cmd"
    ) &
  done
  wait
}

# ------------------------------
# CLEANUP
# ------------------------------

# Cloud
uninstall_helm_releases cloud observe prometheus tempo my-opentelemetry-collector blackbox-exporter loki
delete_pvcs observe
kubectl delete namespace observe --ignore-not-found
kubectl delete namespace dashboard --ignore-not-found

# Edge
uninstall_helm_releases edge observe prometheus my-opentelemetry-collector blackbox-exporter
delete_pvcs observe
kubectl delete namespace observe --ignore-not-found
kubectl delete -f "$HELM_PATH/tempo/tempo_distributor.yaml" --wait --ignore-not-found
kubectl delete -f "$HELM_PATH/loki/gateway.yaml" --wait --ignore-not-found

# ------------------------------
# REDEPLOY
# ------------------------------

# ---- Cloud ----
kubectl config use-context cloud
kubectl create namespace dashboard || true
kubectl create namespace observe || true

helm_install_parallel \
  "helm install prometheus prometheus-community/kube-prometheus-stack -n observe --values $HELM_PATH/prometheus/values_cloud.yaml --create-namespace --version 75.12.0" \
  "helm install tempo -n observe grafana/tempo-distributed --values $HELM_PATH/tempo/values.yaml --create-namespace --version 1.48.0" \
  "helm install loki grafana/loki -n observe -f $HELM_PATH/loki/values.yaml --version 6.42.0"

# Wait only for critical pods
wait_for_critical_pods observe \
  "app.kubernetes.io/name=prometheus" \
  "app.kubernetes.io/name=tempo-distributor"

helm_install_parallel \
  "helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector -f $HELM_PATH/otel/values_cloud.yaml -n observe --version 0.129.0" \
  "helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter -n observe --values $HELM_PATH/prometheus/blackbox_exporter.yaml --version 11.3.1"

# ---- Edge ----
kubectl config use-context edge
kubectl create namespace observe || true

helm_install_parallel \
  "helm install prometheus prometheus-community/kube-prometheus-stack -n observe --values $HELM_PATH/prometheus/values_edge.yaml --create-namespace --version 75.12.0" \
  "helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector -f $HELM_PATH/otel/values_edge.yaml -n observe --version 0.129.0 --create-namespace" \
  "helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter -n observe --values $HELM_PATH/prometheus/blackbox_exporter.yaml --version 11.3.1 --create-namespace"

kubectl apply -f "$HELM_PATH/tempo/tempo_distributor.yaml"
kubectl apply -f "$HELM_PATH/loki/gateway.yaml"
