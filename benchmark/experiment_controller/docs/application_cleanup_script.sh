#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLICATION_DIR="$SCRIPT_DIR/../../../applications/sesa/search_and_rescue/object_classification/deployment/"

# Cloud part
kubectl config use-context cloud
kubectl delete -f "$APPLICATION_DIR/cloud_service/rabbitmq_k8s.yaml" --wait --ignore-not-found
kubectl delete -f "$APPLICATION_DIR/cloud_service/scylladb.yaml" --wait --ignore-not-found
kubectl delete -f "$APPLICATION_DIR/cloud_service/ml_consumer.yaml" --wait --ignore-not-found

kubectl delete pvc persistence-rabbitmq-server-0 --wait --ignore-not-found
kubectl delete pvc scylla-data-scylla-0 --wait --ignore-not-found

kubectl apply -f "$APPLICATION_DIR/cloud_service/rabbitmq_k8s.yaml"
kubectl apply -f "$APPLICATION_DIR/cloud_service/scylladb.yaml"
kubectl wait --for=condition=Ready pod --all --timeout=300s
sleep 5

#NOTE: because rabbitmq operator doesn't support setting specific nodePort yet so we have to patch this to get a consistent nodePort
kubectl patch service rabbitmq \
  -n default \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/ports/0/nodePort", "value": 30072}]'

kubectl exec -i scylla-0 -- cqlsh <<EOF
CREATE KEYSPACE IF NOT EXISTS object_detection
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE object_detection.results (
    id UUID PRIMARY KEY,
    timestamp timestamp,
    prediction text,
    confidence double
);
EOF

kubectl apply -f "$APPLICATION_DIR/cloud_service/ml_consumer.yaml"

# Edge part
kubectl config use-context edge
bash "$APPLICATION_DIR/edge/remove.sh"
echo "Waiting for all terminating pods to be deleted..."
while true; do
  terminating=$(kubectl get pods --field-selector=status.phase=Terminating --no-headers 2>/dev/null)
  if [[ -z "$terminating" ]]; then
    echo "✅ All terminating pods deleted."
    break
  else
    echo "⏳ Waiting for pods to terminate..."
    sleep 5
  fi
done
bash "$APPLICATION_DIR/edge/apply.sh"
kubectl wait --for=condition=Ready pod --all --timeout=300s
