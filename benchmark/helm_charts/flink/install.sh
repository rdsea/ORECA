#!/bin/bash
helm repo add flink-operator-repo https://downloads.apache.org/flink/flink-kubernetes-operator-1.12.1/
helm install -f helm-values.yaml flink-kubernetes-operator flink-operator-repo/flink-kubernetes-operator
