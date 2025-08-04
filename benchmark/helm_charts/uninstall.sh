#!/bin/bash

# Observe
helm uninstall -n observe prometheus
helm uninstall -n observe jaeger
helm uninstall -n observe my-opentelemetry-collector

# Redpanda
helm uninstall -n redpanda redpanda

# Chaos-mesh
helm uninstall -n chaos-mesh chaos-mesh

# Cert-manager
helm uninstall -n cert-manager cert-manager

# Longhorn
kubectl -n longhorn-system patch -p '{"value": "true"}' --type=merge lhs deleting-confirmation-flag
helm uninstall -n longhorn-system longhorn

# Cilium
helm uninstall -n kube-system cilium

# Metallb for getting external ip
kubectl delete -f https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml
kubectl delete -n metallb-system ipaddresspools.metallb.io default-ipaddresspool
kubectl delete -n metallb-system l2advertisements.metallb.io default-advertisement

# Install gateway-api
kubectl delete -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml

# Metric server
kubectl delete -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
