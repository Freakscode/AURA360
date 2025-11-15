#!/usr/bin/env bash
# Deploys the Django API to Cloud Run using gcloud CLI.
set -euo pipefail

if [[ -z "${GCP_PROJECT:-}" ]]; then
  echo "[deploy-api] GCP_PROJECT no está definido" >&2
  exit 1
fi

GCP_REGION=${GCP_REGION:-us-central1}
API_SERVICE_NAME=${API_SERVICE_NAME:-aura360-api}
API_IMAGE_NAME=${API_IMAGE_NAME:-aura360-api}
IMAGE_TAG=${IMAGE_TAG:-"$(git rev-parse --short HEAD)-$(date +%Y%m%d%H%M)"}
API_SOURCE_DIR=${API_SOURCE_DIR:-services/api}
API_ENV_FILE=${API_ENV_FILE:-}
API_SERVICE_ACCOUNT=${API_SERVICE_ACCOUNT:-}

resolve_image_uri() {
  local image="$1"
  if [[ "$image" == gcr.io/* || "$image" == *.pkg.dev/* ]]; then
    echo "${image}:${IMAGE_TAG}"
  else
    echo "gcr.io/${GCP_PROJECT}/${image}:${IMAGE_TAG}"
  fi
}

IMAGE_URI="$(resolve_image_uri "${API_IMAGE_NAME}")"

echo "[deploy-api] Construyendo imagen ${IMAGE_URI}"
echo "[deploy-api] Usando contexto raíz para incluir dependencias compartidas"

# Create temporary cloudbuild.yaml
cat > /tmp/cloudbuild-api.yaml <<EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', '${IMAGE_URI}', '-f', 'services/api/Dockerfile.gcloud', '.']
images:
  - '${IMAGE_URI}'
EOF

gcloud builds submit . \
  --project "${GCP_PROJECT}" \
  --config /tmp/cloudbuild-api.yaml

rm -f /tmp/cloudbuild-api.yaml

create_env_yaml() {
  local env_file="$1"
  local yaml_file="$2"

  echo "# Auto-generated env vars for Cloud Run" > "$yaml_file"
  echo "DJANGO_SETTINGS_MODULE: config.settings" >> "$yaml_file"

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

ENV_YAML_FILE="/tmp/api-env-vars.yaml"
create_env_yaml "$API_ENV_FILE" "$ENV_YAML_FILE"
ENV_FLAG=(--env-vars-file "$ENV_YAML_FILE")

DEPLOY_ARGS=(
  --project "${GCP_PROJECT}"
  --region "${GCP_REGION}"
  --platform managed
  --image "${IMAGE_URI}"
  --port 8000
  --memory "${API_MEMORY:-1Gi}"
  --cpu "${API_CPU:-1}"
  --min-instances "${API_MIN_INSTANCES:-0}"
  --max-instances "${API_MAX_INSTANCES:-3}"
  --allow-unauthenticated
  --timeout "${API_REQUEST_TIMEOUT:-300}"
  --concurrency "${API_CONCURRENCY:-80}"
)

if [[ -n "${API_SERVICE_ACCOUNT}" ]]; then
  DEPLOY_ARGS+=(--service-account "${API_SERVICE_ACCOUNT}")
fi

if [[ -n "${API_VPC_CONNECTOR:-}" ]]; then
  DEPLOY_ARGS+=(--vpc-connector "${API_VPC_CONNECTOR}")
fi

echo "[deploy-api] Desplegando Cloud Run ${API_SERVICE_NAME}"
gcloud run deploy "${API_SERVICE_NAME}" \
  "${DEPLOY_ARGS[@]}" \
  "${ENV_FLAG[@]}"

# Cleanup
rm -f "$ENV_YAML_FILE"

echo "[deploy-api] URL del servicio:"
gcloud run services describe "${API_SERVICE_NAME}" \
  --project "${GCP_PROJECT}" \
  --region "${GCP_REGION}" \
  --format 'value(status.url)'
