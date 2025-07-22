#!/bin/bash

helm install cilium cilium/cilium --version 1.17.5 \
  --namespace kube-system --values cilium_values.yaml
