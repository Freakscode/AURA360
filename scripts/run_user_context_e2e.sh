#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/services/vectordb/docker-compose.e2e.yml"
COMPOSE_CMD=(docker compose -f "$COMPOSE_FILE")

function cleanup {
  echo "\nStopping vectordb E2E stack..."
  "${COMPOSE_CMD[@]}" down -v --remove-orphans
}

trap cleanup EXIT

echo "Building and starting vectordb E2E stack..."
"${COMPOSE_CMD[@]}" up -d --build qdrant redis vectordb-api vectordb-worker

function wait_for_http {
  local url=$1
  local retries=${2:-30}
  local delay=${3:-5}
  for ((i=1; i<=retries; i++)); do
    if curl -fsS "$url" >/dev/null; then
      echo "Service healthy: $url"
      return 0
    fi
    echo "Waiting for $url ($i/$retries)..."
    sleep "$delay"
  done
  echo "Timeout waiting for $url" >&2
  return 1
}

wait_for_http "http://localhost:6333/healthz"
wait_for_http "http://localhost:8001/readyz"

cd "$ROOT_DIR"

echo "Running user context E2E script..."
python3 test_user_context_e2e.py
