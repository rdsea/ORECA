#!/bin/bash
# Clean up
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELM_CHART_DIR="$SCRIPT_DIR/../../../../../applications/train-ticket/helm_charts/"

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
kubectl delete -f "$HELM_CHART_DIR/cilium/observability_route.yaml"
kubectl delete -f "$HELM_CHART_DIR/cilium/gateway.yaml"

# Uninstall Helm releases

uninstall_helm_releases cloud observe otel-collector tempo blackbox-exporter prometheus beyla

kubectl delete pvc -n observe --all
kubectl delete namespace observe --ignore-not-found

echo "Finished cleaning up."
echo "Start redeploying"
# Redeploy
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: observe
  labels:
    pod-security.kubernetes.io/enforce: privileged
EOF

helm install prometheus prometheus-community/kube-prometheus-stack -n observe \
  --values "$HELM_CHART_DIR/prometheus/values_distributed.yaml" --version 75.12.0 \
  --create-namespace

helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter \
  -n observe --values "$HELM_CHART_DIR/prometheus/blackbox_exporter.yaml" --version 11.3.1

kubectl wait --for=condition=Ready pod --all --timeout=180s --namespace observe

helm install tempo -n observe grafana/tempo-distributed \
  --values "$HELM_CHART_DIR/tempo/values_distributed.yaml" --create-namespace

helm install otel-collector open-telemetry/opentelemetry-collector \
  -f "$HELM_CHART_DIR/otel/values.yaml" -n observe --version 0.129.0 \
  --set config.exporters.otlp.endpoint="http://tempo-distributor.observe:4317"

helm install beyla -n observe --create-namespace grafana/beyla \
  -f "$HELM_CHART_DIR/beyla/values.yaml"

kubectl wait --for=condition=Ready pod --all --timeout=180s --namespace observe

kubectl apply -f "$HELM_CHART_DIR/cilium/gateway.yaml"
sleep 5
kubectl apply -f "$HELM_CHART_DIR/cilium/observability_route.yaml"
