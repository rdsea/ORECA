#!/bin/bash

set -e
kubectl config use-context cloud
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HELM_CHART_DIR="$SCRIPT_DIR/../benchmark/helm_charts/"
ADDR_POOL="
   - <ip>-<ip 
"

helm repo add cilium https://helm.cilium.io/
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add longhorn https://charts.longhorn.io
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm repo update

# Metallb for getting external ip
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml

# Install gateway-api
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml

# Cilium
helm install cilium cilium/cilium --version 1.17.5 \
  --namespace kube-system --values "$HELM_CHART_DIR/cilium/values_cloud.yaml"
kubectl wait --namespace kube-system --for=condition=Ready pod --all --timeout=300s

kubectl apply -f - <<EOF
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-ipaddresspool
  namespace: metallb-system
spec:
  addresses:
${ADDR_POOL}
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default-advertisement
  namespace: metallb-system
EOF

# Prometheus
kubectl create namespace dashboard || true
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n observe --values "$HELM_CHART_DIR/prometheus/values_cloud.yaml" --create-namespace --version 75.12.0

# Longhorn
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system --create-namespace --version 1.9.0 --values "$HELM_CHART_DIR/longhorn/values.yaml"
kubectl wait --namespace longhorn-system --for=condition=Ready pod --all --timeout=300s

# Blackbox exporter
helm install blackbox-exporter prometheus-community/prometheus-blackbox-exporter \
  -n observe --values "$HELM_PATH/prometheus/blackbox_exporter.yaml" --version 11.3.1

# Otel collector
helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector \
  -f "$HELM_CHART_DIR/otel/values_cloud.yaml" -n observe --version 0.129.0
kubectl wait --namespace observe --for=condition=Available deploy --all --timeout=300s

# Rabbitmq operator
kubectl apply -f "https://github.com/rabbitmq/cluster-operator/releases/latest/download/cluster-operator.yml"
