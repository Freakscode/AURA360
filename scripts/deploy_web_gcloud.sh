#!/usr/bin/env bash
# Builds the Angular frontend and uploads artifacts to a Cloud Storage bucket.
set -euo pipefail

if [[ -z "${GCP_PROJECT:-}" ]]; then
  echo "[deploy-web] GCP_PROJECT no está definido" >&2
  exit 1
fi

if [[ -z "${WEB_BUCKET:-}" ]]; then
  echo "[deploy-web] WEB_BUCKET no está definido (ej. aura360-web-static)" >&2
  exit 1
fi

GCP_REGION=${GCP_REGION:-us-central1}
WEB_DIR=${WEB_DIR:-apps/web}
WEB_DIST_DIR=${WEB_DIST_DIR:-dist/aura360-front/browser}
WEB_BUILD_COMMAND=${WEB_BUILD_COMMAND:-"npm run build"}
WEB_INSTALL_COMMAND=${WEB_INSTALL_COMMAND:-"npm ci"}
WEB_CACHE_CONTROL=${WEB_CACHE_CONTROL:-"public,max-age=300"}

pushd "$WEB_DIR" >/dev/null

if [[ "${WEB_SKIP_INSTALL:-false}" != "true" ]]; then
  echo "[deploy-web] Ejecutando ${WEB_INSTALL_COMMAND}"
  eval "$WEB_INSTALL_COMMAND"
fi

echo "[deploy-web] Ejecutando ${WEB_BUILD_COMMAND}"
eval "$WEB_BUILD_COMMAND"

popd >/dev/null

DIST_PATH="${WEB_DIR}/${WEB_DIST_DIR}"
if [[ ! -d "$DIST_PATH" ]]; then
  echo "[deploy-web] No se encontró ${DIST_PATH}. Verifica la configuración de Angular." >&2
  exit 1
fi

BUCKET_URI="gs://${WEB_BUCKET}"
if ! gcloud storage buckets describe "$BUCKET_URI" --project "$GCP_PROJECT" >/dev/null 2>&1; then
  echo "[deploy-web] Creando bucket ${BUCKET_URI}"
  gcloud storage buckets create "$BUCKET_URI" \
    --project "$GCP_PROJECT" \
    --location "$GCP_REGION" \
    --uniform-bucket-level-access
fi

echo "[deploy-web] Configurando bucket para hosting estático"
gcloud storage buckets update "$BUCKET_URI" \
  --web-main-page-suffix index.html \
  --web-error-page index.html >/dev/null

echo "[deploy-web] Subiendo archivos de ${DIST_PATH}"
# Primero eliminar archivos antiguos (excepto los que coinciden)
# Luego sincronizar
gcloud storage rsync \
  "$DIST_PATH" \
  "$BUCKET_URI" \
  --recursive

echo "[deploy-web] Aplicando encabezado Cache-Control=${WEB_CACHE_CONTROL}"
gsutil -m setmeta -h "Cache-Control:${WEB_CACHE_CONTROL}" "${BUCKET_URI}/**" >/dev/null

echo "[deploy-web] Deployment estático completado. URL base: https://storage.googleapis.com/${WEB_BUCKET}/index.html"
