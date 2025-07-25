#!/bin/bash

# Metallb for getting external ip
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml

# Install gateway-api
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml

# Metric server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Cilium
# helm install cilium cilium/cilium --version 1.17.5 --namespace kube-system --values cilium_values.yml

# Longhorn
# helm repo add longhorn https://charts.longhorn.io
# helm repo update
# helm install longhorn longhorn/longhorn --namespace longhorn-system --create-namespace --version 1.9.0 --values values.yaml
#
# Otel collector
# helm repo add open-telemetry https://open-telemetry.github.io/opentelemetry-helm-charts
helm install my-opentelemetry-collector open-telemetry/opentelemetry-collector \
  --set image.repository="otel/opentelemetry-collector-k8s" \
  --set mode=daemonset
