#!/usr/bin/env bash
# Script unificado para desplegar todos los servicios de AURA360 a Google Cloud
set -euo pipefail

echo "=========================================="
echo "  AURA360 - Despliegue a Google Cloud"
echo "=========================================="
echo ""

# Configuración
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export API_ENV_FILE="services/api/.env.production"
export WORKER_ENV_FILE="services/api/.env.production"
export WEB_BUCKET="aura360-web-prod"

echo "Proyecto: ${GCP_PROJECT}"
echo "Región: ${GCP_REGION}"
echo ""

# Verificar autenticación
echo "Verificando autenticación..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Error: No hay cuenta autenticada. Ejecuta: gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo "Cuenta activa: ${ACTIVE_ACCOUNT}"
echo ""

# Preguntar qué servicios desplegar
echo "¿Qué servicios deseas desplegar?"
echo "1) Todos (API + Worker + Web)"
echo "2) Solo Backend (API + Worker)"
echo "3) Solo API"
echo "4) Solo Worker"
echo "5) Solo Web"
read -p "Selecciona una opción (1-5): " OPTION

DEPLOY_API=false
DEPLOY_WORKER=false
DEPLOY_WEB=false

case $OPTION in
    1)
        DEPLOY_API=true
        DEPLOY_WORKER=true
        DEPLOY_WEB=true
        ;;
    2)
        DEPLOY_API=true
        DEPLOY_WORKER=true
        ;;
    3)
        DEPLOY_API=true
        ;;
    4)
        DEPLOY_WORKER=true
        ;;
    5)
        DEPLOY_WEB=true
        ;;
    *)
        echo "Opción inválida"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Iniciando despliegue..."
echo "=========================================="
echo ""

# Desplegar API
if [ "$DEPLOY_API" = true ]; then
    echo "──────────────────────────────────────────"
    echo "📦 Desplegando API a Cloud Run..."
    echo "──────────────────────────────────────────"
    if ./scripts/deploy_api_gcloud.sh; then
        echo "✅ API desplegada exitosamente"
    else
        echo "❌ Error desplegando API"
        exit 1
    fi
    echo ""
fi

# Desplegar Worker
if [ "$DEPLOY_WORKER" = true ]; then
    echo "──────────────────────────────────────────"
    echo "⚙️  Desplegando Worker (Celery) a Cloud Run..."
    echo "──────────────────────────────────────────"
    if ./scripts/deploy_worker_gcloud.sh; then
        echo "✅ Worker desplegado exitosamente"
    else
        echo "❌ Error desplegando Worker"
        exit 1
    fi
    echo ""
fi

# Desplegar Web
if [ "$DEPLOY_WEB" = true ]; then
    echo "──────────────────────────────────────────"
    echo "🌐 Desplegando Web a Cloud Storage..."
    echo "──────────────────────────────────────────"
    if ./scripts/deploy_web_gcloud.sh; then
        echo "✅ Web desplegada exitosamente"
    else
        echo "❌ Error desplegando Web"
        exit 1
    fi
    echo ""
fi

echo ""
echo "=========================================="
echo "  ✅ Despliegue completado"
echo "=========================================="
echo ""

# Mostrar URLs de los servicios
echo "URLs de los servicios desplegados:"
echo ""

if [ "$DEPLOY_API" = true ]; then
    echo "📦 API:"
    gcloud run services describe aura360-api \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(status.url)' 2>/dev/null || echo "  (No disponible aún)"
    echo ""
fi

if [ "$DEPLOY_WORKER" = true ]; then
    echo "⚙️  Worker:"
    gcloud run services describe aura360-celery \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(status.url)' 2>/dev/null || echo "  (No disponible aún)"
    echo ""
fi

if [ "$DEPLOY_WEB" = true ]; then
    echo "🌐 Web:"
    echo "  https://storage.googleapis.com/${WEB_BUCKET}/index.html"
    echo ""
fi

echo "=========================================="
echo "Siguiente paso: Verificar health checks"
echo "=========================================="
echo ""
echo "Para verificar que los servicios están funcionando:"
echo ""
if [ "$DEPLOY_API" = true ]; then
    API_URL=$(gcloud run services describe aura360-api \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(status.url)' 2>/dev/null)
    if [ -n "$API_URL" ]; then
        echo "curl ${API_URL}/api/v1/health"
    fi
fi
echo ""
