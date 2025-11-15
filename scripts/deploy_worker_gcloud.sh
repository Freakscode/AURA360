#!/usr/bin/env bash
# Deploys the Celery worker (Cloud Run service) via gcloud CLI.
set -euo pipefail

if [[ -z "${GCP_PROJECT:-}" ]]; then
  echo "[deploy-worker] GCP_PROJECT no está definido" >&2
  exit 1
fi

GCP_REGION=${GCP_REGION:-us-central1}
WORKER_SERVICE_NAME=${WORKER_SERVICE_NAME:-aura360-celery}
WORKER_IMAGE_NAME=${WORKER_IMAGE_NAME:-aura360-api}
IMAGE_TAG=${IMAGE_TAG:-"$(git rev-parse --short HEAD)-$(date +%Y%m%d%H%M)"}
SOURCE_DIR=${WORKER_SOURCE_DIR:-services/api}
WORKER_ENV_FILE=${WORKER_ENV_FILE:-}
WORKER_SERVICE_ACCOUNT=${WORKER_SERVICE_ACCOUNT:-}

resolve_image_uri() {
  local image="$1"
  if [[ "$image" == gcr.io/* || "$image" == *.pkg.dev/* ]]; then
    echo "${image}:${IMAGE_TAG}"
  else
    echo "gcr.io/${GCP_PROJECT}/${image}:${IMAGE_TAG}"
  fi
}

IMAGE_URI="$(resolve_image_uri "${WORKER_IMAGE_NAME}")"

echo "[deploy-worker] Construyendo imagen ${IMAGE_URI}"
echo "[deploy-worker] Usando contexto raíz para incluir dependencias compartidas"

# Create temporary cloudbuild.yaml
cat > /tmp/cloudbuild-worker.yaml <<EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${IMAGE_URI}', '-f', 'services/api/Dockerfile.gcloud', '.']
images:
  - '${IMAGE_URI}'
EOF

gcloud builds submit . \
  --project "${GCP_PROJECT}" \
  --config /tmp/cloudbuild-worker.yaml

rm -f /tmp/cloudbuild-worker.yaml

create_env_yaml() {
  local env_file="$1"
  local yaml_file="$2"

  echo "# Auto-generated env vars for Cloud Run" > "$yaml_file"
  echo "DJANGO_SETTINGS_MODULE: config.settings" >> "$yaml_file"
  echo "CELERY_QUEUE: ${CELERY_QUEUE:-holistic_snapshots}" >> "$yaml_file"
  echo "CELERY_CONCURRENCY: ${CELERY_CONCURRENCY:-2}" >> "$yaml_file"

  if [[ -z "$env_file" || ! -f "$env_file" ]]; then
    return
  fi

  while IFS= read -r raw_line || [[ -n "$raw_line" ]]; do
    local line="${raw_line%%#*}"
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue
    local key="${line%%=*}"
    local value="${line#*=}"
    key="$(echo "$key" | xargs)"
    value="$(echo "$value" | xargs)"
    # Escape special characters for YAML
    value="${value//\\/\\\\}"
    value="${value//\"/\\\"}"
    echo "${key}: \"${value}\"" >> "$yaml_file"
  done < "$env_file"
}

ENV_YAML_FILE="/tmp/worker-env-vars.yaml"
create_env_yaml "$WORKER_ENV_FILE" "$ENV_YAML_FILE"
ENV_FLAG=(--env-vars-file "$ENV_YAML_FILE")

DEPLOY_ARGS=(
  --project "${GCP_PROJECT}"
  --region "${GCP_REGION}"
  --platform managed
  --image "${IMAGE_URI}"
  --no-allow-unauthenticated
  --min-instances "${WORKER_MIN_INSTANCES:-1}"
  --max-instances "${WORKER_MAX_INSTANCES:-1}"
  --memory "${WORKER_MEMORY:-1Gi}"
  --cpu "${WORKER_CPU:-1}"
  --timeout "${WORKER_REQUEST_TIMEOUT:-3600}"
  --command "/bin/bash"
  --args "/app/scripts/start_celery_worker.sh"
)

if [[ -n "${WORKER_SERVICE_ACCOUNT}" ]]; then
  DEPLOY_ARGS+=(--service-account "${WORKER_SERVICE_ACCOUNT}")
fi

if [[ -n "${WORKER_VPC_CONNECTOR:-}" ]]; then
  DEPLOY_ARGS+=(--vpc-connector "${WORKER_VPC_CONNECTOR}")
fi

echo "[deploy-worker] Desplegando Cloud Run ${WORKER_SERVICE_NAME}"
gcloud run deploy "${WORKER_SERVICE_NAME}" \
  "${DEPLOY_ARGS[@]}" \
  "${ENV_FLAG[@]}"

# Cleanup
rm -f "$ENV_YAML_FILE"

gcloud run services describe "${WORKER_SERVICE_NAME}" \
  --project "${GCP_PROJECT}" \
  --region "${GCP_REGION}" \
  --format 'value(status.url)'
