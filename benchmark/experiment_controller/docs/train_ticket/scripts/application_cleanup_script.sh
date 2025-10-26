#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRAIN_TICKET_SOURCE="$SCRIPT_DIR/../../../../../applications/train-ticket/train-ticket"
#
# Check if the directory is empty
if [ -z "$(ls -A "$TRAIN_TICKET_SOURCE")" ]; then
  echo "Error: Directory '$TRAIN_TICKET_SOURCE' is empty.  Run git submodule update --init"
  exit 1
fi

cd "$TRAIN_TICKET_SOURCE" || exit 1
make reset-deploy Namespace=train-ticket
kubectl delete ns train-ticket

sleep 5
kubectl apply -f - <<EOF
apiVersion: v1
kind: Namespace
metadata:
  name: train-ticket
  labels:
    pod-security.kubernetes.io/enforce: privileged
EOF
make deploy Namespace=train-ticket
kubectl wait --for=condition=Ready pod --all --timeout=300s --namespace train-ticket
