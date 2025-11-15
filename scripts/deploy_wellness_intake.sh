#!/usr/bin/env bash
# Script específico para desplegar el formulario de wellness intake
# Este script despliega el frontend Angular con la configuración correcta para producción
set -euo pipefail

echo "=========================================="
echo "  Despliegue del Formulario Wellness Intake"
echo "=========================================="
echo ""

# Configuración
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export WEB_BUCKET="aura360-web-prod"

# Obtener URL del API desplegado
echo "Obteniendo URL del API..."
API_URL=$(gcloud run services describe aura360-api \
  --project "${GCP_PROJECT}" \
  --region "${GCP_REGION}" \
  --format 'value(status.url)' 2>/dev/null || echo "")

if [[ -z "$API_URL" ]]; then
  echo "⚠️  Advertencia: No se encontró el servicio API desplegado."
  echo "   El formulario usará la URL configurada en environment.ts"
  echo ""
else
  echo "✅ API encontrado: ${API_URL}"
  echo ""
  
  # Actualizar environment.ts con la URL del API
  echo "Actualizando configuración de producción..."
  API_BASE_URL="${API_URL}/api"
  
  # Crear backup del environment.ts
  cp apps/web/src/environments/environment.ts apps/web/src/environments/environment.ts.backup
  
  # Actualizar apiBaseUrl en environment.ts
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|apiBaseUrl:.*|apiBaseUrl: '${API_BASE_URL}',|" apps/web/src/environments/environment.ts
  else
    # Linux
    sed -i "s|apiBaseUrl:.*|apiBaseUrl: '${API_BASE_URL}',|" apps/web/src/environments/environment.ts
  fi
  
  echo "✅ Configuración actualizada: apiBaseUrl = ${API_BASE_URL}"
  echo ""
fi

# Desplegar el frontend
echo "=========================================="
echo "Desplegando frontend a Cloud Storage..."
echo "=========================================="
echo ""

if ./scripts/deploy_web_gcloud.sh; then
  echo ""
  echo "✅ Frontend desplegado exitosamente"
  echo ""
  
  # Restaurar backup si existe
  if [[ -f "apps/web/src/environments/environment.ts.backup" ]]; then
    mv apps/web/src/environments/environment.ts.backup apps/web/src/environments/environment.ts
    echo "✅ Configuración restaurada"
  fi
  
  echo ""
  echo "=========================================="
  echo "  ✅ Despliegue completado"
  echo "=========================================="
  echo ""
  echo "URLs del formulario:"
  echo "  - Formulario: https://storage.googleapis.com/${WEB_BUCKET}/index.html#/public/wellness-intake"
  echo "  - Directo: https://storage.googleapis.com/${WEB_BUCKET}/public/wellness-intake"
  echo ""
  echo "Nota: Cloud Storage sirve archivos estáticos. Para rutas SPA, asegúrate de que"
  echo "el bucket tenga configurado 'index.html' como página de error (ya configurado)."
  echo ""
else
  echo ""
  echo "❌ Error en el despliegue"
  
  # Restaurar backup si existe
  if [[ -f "apps/web/src/environments/environment.ts.backup" ]]; then
    mv apps/web/src/environments/environment.ts.backup apps/web/src/environments/environment.ts
    echo "✅ Configuración restaurada"
  fi
  
  exit 1
fi

