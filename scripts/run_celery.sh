#!/usr/bin/env bash
set -euo pipefail

MODE=${1:-worker}
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT/services/api"

export DJANGO_SETTINGS_MODULE="config.settings"
export PYTHONPATH="$PROJECT_ROOT/services/api:$PYTHONPATH"

case "$MODE" in
  worker)
    echo "Starting Celery worker (queues: api_default, holistic_snapshots)..."
    uv run celery -A config worker -l info -Q api_default,holistic_snapshots
    ;;
  beat)
    echo "Starting Celery beat scheduler..."
    uv run celery -A config beat -l info
    ;;
  both)
    echo "Starting Celery worker and beat using two processes..."
    uv run celery -A config worker -l info -Q api_default,holistic_snapshots &
    WORKER_PID=$!
    trap 'kill $WORKER_PID' EXIT
    uv run celery -A config beat -l info
    ;;
  *)
    echo "Usage: $0 [worker|beat|both]" >&2
    exit 1
    ;;
 esac
