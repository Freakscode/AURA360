#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-8080}
CELERY_QUEUE=${CELERY_QUEUE:-holistic_snapshots}
CELERY_CONCURRENCY=${CELERY_CONCURRENCY:-2}

echo "[celery-worker] Booting worker for queue=${CELERY_QUEUE} (concurrency=${CELERY_CONCURRENCY})"

celery -A config worker \
  --loglevel=info \
  --queues="${CELERY_QUEUE}" \
  --concurrency="${CELERY_CONCURRENCY}" &

CELERY_PID=$!

cleanup() {
  echo "[celery-worker] Shutting down (PID ${CELERY_PID})"
  kill "$CELERY_PID"
  wait "$CELERY_PID"
}

trap cleanup EXIT INT TERM

echo "[celery-worker] Exposing lightweight HTTP server on port ${PORT} for Cloud Run health checks"
python -m http.server "$PORT"
