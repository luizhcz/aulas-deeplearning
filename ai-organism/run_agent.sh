#!/usr/bin/env bash
set -euo pipefail

# Example:
#   export REGISTRY_URL=http://localhost:9100
#   export AGENT_BASE_URL=http://localhost:9002
#   export MODEL_PROVIDER=ollama
#   export MODEL_NAME=llama3.1:8b
#   export OLLAMA_BASE_URL=http://localhost:11434
#
# Run:
#   ./run_agent.sh agents.trading.order_placement.main:app 9002

APP="${1:-}"
PORT="${2:-9001}"

if [[ -z "$APP" ]]; then
  echo "Usage: $0 <module:app> <port>"
  exit 1
fi

uvicorn --app-dir src "$APP" --host 0.0.0.0 --port "$PORT"