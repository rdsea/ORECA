#!/bin/bash
# Clean up
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAIN_TICKET_SOURCE="$SCRIPT_DIR/../../../../../applications/train-ticket/helm_charts/"
kubectl delete -f "$HELM_CHART_DIR/cilium/observability_route.yaml"
kubectl delete -f "$HELM_CHART_DIR/cilium/gateway.yaml"

# Uninstall Helm releases
helm uninstall otel-collector -n observe
helm uninstall tempo -n observe
helm uninstall blackbox-exporter -n observe
helm uninstall prometheus -n observe
helm uninstall beyla -n observe

kubectl delete pvc -n observe --all
kubectl delete namespace observe --ignore-not-found
# Redeploy
helm install prometheus prometheus-community/kube-prometheus-stack -n observe \
  --values "$HELM_CHART_DIR/prometheus/values_distributed.yaml" --version 75.12.0 \
  --create-namespace

helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter \
  -n observe --values "$HELM_CHART_DIR/prometheus/blackbox_exporter.yaml" --version 11.3.1

helm install tempo -n observe grafana/tempo-distributed \
  --values "$HELM_CHART_DIR/tempo/values_distributed.yaml" --create-namespace

helm install otel-collector open-telemetry/opentelemetry-collector \
  -f "$HELM_CHART_DIR/otel/values.yaml" -n observe --version 0.129.0 \
  --set config.exporters.otlp.endpoint="http://tempo-distributor.observe:4317"

helm install beyla -n observe --create-namespace grafana/beyla \
  -f "$HELM_CHART_DIR/beyla/values.yaml"

kubectl apply -f "$HELM_CHART_DIR/cilium/gateway.yaml"
kubectl apply -f "$HELM_CHART_DIR/cilium/observability_route.yaml"
