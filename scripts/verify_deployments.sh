#!/usr/bin/env bash
# Script para verificar el estado de todos los despliegues de AURA360 en Google Cloud
set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuración
export GCP_PROJECT="${GCP_PROJECT:-aura-360-471711}"
export GCP_REGION="${GCP_REGION:-us-central1}"

echo ""
echo "=========================================="
echo "  🔍 AURA360 - Verificación de Despliegues"
echo "=========================================="
echo ""
echo "Proyecto: ${GCP_PROJECT}"
echo "Región: ${GCP_REGION}"
echo ""

# Verificar autenticación
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Verificando autenticación..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Error: No hay cuenta autenticada${NC}"
    echo "Ejecuta: gcloud auth login"
    exit 1
fi

ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")
echo -e "${GREEN}✅ Cuenta activa: ${ACTIVE_ACCOUNT}${NC}"
echo ""

# Función para verificar servicio de Cloud Run
check_cloud_run_service() {
    local service_name=$1
    local display_name=$2
    
    echo "──────────────────────────────────────────"
    echo -e "${BOLD}📦 ${display_name}${NC}"
    echo "──────────────────────────────────────────"
    
    if ! gcloud run services describe "$service_name" \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format json &>/dev/null; then
        echo -e "${RED}❌ Servicio NO desplegado${NC}"
        echo ""
        return 1
    fi
    
    # Obtener información del servicio
    local url=$(gcloud run services describe "$service_name" \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(status.url)' 2>/dev/null)
    
    local status=$(gcloud run services describe "$service_name" \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(status.conditions[0].status)' 2>/dev/null)
    
    local last_deployed=$(gcloud run services describe "$service_name" \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(metadata.annotations."run.googleapis.com/lastModified")' 2>/dev/null)
    
    local image=$(gcloud run services describe "$service_name" \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(spec.template.spec.containers[0].image)' 2>/dev/null)
    
    local instances=$(gcloud run services describe "$service_name" \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format 'value(spec.template.spec.containerConcurrency)' 2>/dev/null)
    
    echo -e "URL:            ${BLUE}${url}${NC}"
    echo "Estado:         ${status}"
    echo "Última deploy:  ${last_deployed}"
    echo "Imagen:         ${image}"
    
    # Verificar estado
    if [ "$status" = "True" ]; then
        echo -e "Health:         ${GREEN}✅ Saludable${NC}"
    else
        echo -e "Health:         ${RED}❌ No saludable${NC}"
    fi
    
    # Verificar health check si está disponible
    if [[ "$url" != "" ]]; then
        echo ""
        echo "Probando health check..."
        
        # Intentar varios endpoints comunes
        local health_endpoints=("/api/v1/health" "/health" "/readyz" "/healthz")
        local health_ok=false
        
        for endpoint in "${health_endpoints[@]}"; do
            if curl -f -s -m 5 "${url}${endpoint}" &>/dev/null; then
                echo -e "${GREEN}✅ Health check OK: ${endpoint}${NC}"
                health_ok=true
                break
            fi
        done
        
        if [ "$health_ok" = false ]; then
            echo -e "${YELLOW}⚠️  Health check no disponible en endpoints comunes${NC}"
        fi
    fi
    
    # Mostrar logs recientes (últimas 5 líneas)
    echo ""
    echo "Logs recientes (últimas 5 líneas):"
    echo "---"
    gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=${service_name}" \
        --project "${GCP_PROJECT}" \
        --limit 5 \
        --format "table(timestamp,textPayload)" 2>/dev/null || echo "No hay logs disponibles"
    
    echo ""
}

# Función para verificar bucket de Cloud Storage
check_storage_bucket() {
    local bucket_name=$1
    
    echo "──────────────────────────────────────────"
    echo -e "${BOLD}🌐 Web Frontend (Cloud Storage)${NC}"
    echo "──────────────────────────────────────────"
    
    if ! gcloud storage buckets describe "gs://${bucket_name}" \
        --project "${GCP_PROJECT}" &>/dev/null; then
        echo -e "${RED}❌ Bucket NO existe${NC}"
        echo ""
        return 1
    fi
    
    echo -e "${GREEN}✅ Bucket desplegado${NC}"
    echo "Bucket:         gs://${bucket_name}"
    echo "URL:            https://storage.googleapis.com/${bucket_name}/index.html"
    
    # Verificar si tiene archivos
    local file_count=$(gcloud storage ls "gs://${bucket_name}/" --project "${GCP_PROJECT}" 2>/dev/null | wc -l)
    echo "Archivos:       ${file_count}"
    
    # Verificar si index.html existe
    if gcloud storage ls "gs://${bucket_name}/index.html" --project "${GCP_PROJECT}" &>/dev/null; then
        echo -e "index.html:     ${GREEN}✅ Existe${NC}"
        
        # Probar si es accesible
        if curl -f -s -m 5 "https://storage.googleapis.com/${bucket_name}/index.html" &>/dev/null; then
            echo -e "Accesibilidad:  ${GREEN}✅ Accesible públicamente${NC}"
        else
            echo -e "Accesibilidad:  ${RED}❌ No accesible${NC}"
        fi
    else
        echo -e "index.html:     ${RED}❌ No existe${NC}"
    fi
    
    echo ""
}

# Función para verificar recursos relacionados
check_related_resources() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 Recursos Relacionados"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Verificar VPC Connectors
    echo "VPC Connectors:"
    gcloud compute networks vpc-access connectors list \
        --project "${GCP_PROJECT}" \
        --region "${GCP_REGION}" \
        --format "table(name,state,network)" 2>/dev/null || echo "  No hay VPC connectors"
    echo ""
    
    # Verificar secretos en Secret Manager
    echo "Secretos en Secret Manager:"
    gcloud secrets list --project "${GCP_PROJECT}" --limit 10 2>/dev/null || echo "  No hay secretos configurados"
    echo ""
}

# Función para verificar imágenes en Container Registry
check_container_images() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Imágenes de Contenedor"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "Últimas imágenes en GCR:"
    gcloud container images list --repository="gcr.io/${GCP_PROJECT}" --limit 5 2>/dev/null || \
        echo "  No hay imágenes en gcr.io/${GCP_PROJECT}"
    echo ""
    
    # Verificar tags de imágenes específicas
    for image in "aura360-api" "aura360-agents" "aura360-vectordb"; do
        if gcloud container images list --repository="gcr.io/${GCP_PROJECT}" --filter="name:${image}" 2>/dev/null | grep -q "${image}"; then
            echo "Tags para ${image}:"
            gcloud container images list-tags "gcr.io/${GCP_PROJECT}/${image}" --limit 3 2>/dev/null || echo "  Sin tags"
        fi
    done
    echo ""
}

# Función para resumen de costos
check_costs() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "💰 Resumen de Servicios Activos"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "Cloud Run Services:"
    gcloud run services list --project "${GCP_PROJECT}" --region "${GCP_REGION}" 2>/dev/null || echo "  Sin servicios"
    echo ""
    
    echo "Cloud Storage Buckets:"
    gcloud storage buckets list --project "${GCP_PROJECT}" 2>/dev/null || echo "  Sin buckets"
    echo ""
}

# Ejecutar verificaciones
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Servicios de Cloud Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar servicios
check_cloud_run_service "aura360-api" "API Django"
check_cloud_run_service "aura360-celery" "Worker Celery"
check_cloud_run_service "aura360-agents" "Agents Service"
check_cloud_run_service "aura360-vectordb" "VectorDB Service"

# Verificar frontend
check_storage_bucket "aura360-web-prod"

# Verificar recursos relacionados
check_related_resources

# Verificar imágenes
check_container_images

# Resumen de costos
check_costs

# Resumen final
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumen de Verificación"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Contar servicios activos
active_services=0
if gcloud run services describe "aura360-api" --project "${GCP_PROJECT}" --region "${GCP_REGION}" &>/dev/null; then
    ((active_services++))
fi
if gcloud run services describe "aura360-celery" --project "${GCP_PROJECT}" --region "${GCP_REGION}" &>/dev/null; then
    ((active_services++))
fi
if gcloud run services describe "aura360-agents" --project "${GCP_PROJECT}" --region "${GCP_REGION}" &>/dev/null; then
    ((active_services++))
fi
if gcloud run services describe "aura360-vectordb" --project "${GCP_PROJECT}" --region "${GCP_REGION}" &>/dev/null; then
    ((active_services++))
fi

echo "Servicios Cloud Run activos: ${active_services}/4"
if gcloud storage buckets describe "gs://aura360-web-prod" --project "${GCP_PROJECT}" &>/dev/null; then
    echo -e "Frontend Web:                 ${GREEN}✅ Desplegado${NC}"
else
    echo -e "Frontend Web:                 ${RED}❌ No desplegado${NC}"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Verificación completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Para más detalles, visita:"
echo "  https://console.cloud.google.com/run?project=${GCP_PROJECT}"
echo ""

