#!/bin/bash

export PORT=5011

CMD="uvicorn --host XXX.XXX.XXX.XXX --port $PORT ensemble:app"

for value in "$@"; do
  if [[ "$value" == "--debug" ]]; then
    CMD="fastapi dev --host XXX.XXX.XXX.XXX --port $PORT ensemble.py"
    break
  fi
done

$CMD
