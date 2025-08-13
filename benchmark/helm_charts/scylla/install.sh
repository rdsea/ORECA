#!/bin/bash

helm repo add scylla https://scylla-operator-charts.storage.googleapis.com/stable
helm repo update

helm install scylla-operator scylla/scylla-operator --values values.operator.yaml --create-namespace --namespace scylla-operator

helm install scylla scylla/scylla --values examples/helm/values.cluster.yaml --create-namespace --namespace scylla
