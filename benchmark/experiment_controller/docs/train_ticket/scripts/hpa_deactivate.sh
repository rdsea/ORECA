#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kubectl delete -f "$SCRIPT_DIR/hpa.yaml"
