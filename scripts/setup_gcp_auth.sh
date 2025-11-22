#!/bin/bash

###############################################################################
# Script de Configuración de Autenticación GCP
#
# Configura Application Default Credentials (ADC) para desarrollo local
#
# Uso:
#   ./scripts/setup_gcp_auth.sh
###############################################################################

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
GCP_PROJECT="aura-360-471711"

print_header() {
    echo ""
    echo -e "${BLUE}======================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}======================================================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

###############################################################################
# Verificar gcloud CLI
###############################################################################

print_header "Verificando Google Cloud CLI"

if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI no está instalado"
    print_info "Instalar desde: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

print_success "gcloud CLI encontrado: $(gcloud version | head -n 1)"

###############################################################################
# Verificar autenticación actual
###############################################################################

print_header "Verificando Autenticación Actual"

CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || echo "")

if [ -z "$CURRENT_ACCOUNT" ]; then
    print_warning "No estás autenticado con gcloud"
    print_info "Ejecutando: gcloud auth login..."
    gcloud auth login
    CURRENT_ACCOUNT=$(gcloud config get-value account)
fi

print_success "Autenticado como: $CURRENT_ACCOUNT"

###############################################################################
# Configurar Application Default Credentials (ADC)
###############################################################################

print_header "Configurando Application Default Credentials (ADC)"

ADC_FILE="$HOME/.config/gcloud/application_default_credentials.json"

if [ -f "$ADC_FILE" ]; then
    print_info "ADC ya existe: $ADC_FILE"
    print_warning "¿Quieres renovar las credenciales? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_info "Renovando ADC..."
        gcloud auth application-default login
    else
        print_info "Usando ADC existente"
    fi
else
    print_info "Configurando ADC por primera vez..."
    gcloud auth application-default login
fi

if [ -f "$ADC_FILE" ]; then
    print_success "ADC configurado correctamente: $ADC_FILE"
else
    print_error "No se pudo configurar ADC"
    exit 1
fi

###############################################################################
# Configurar proyecto por defecto
###############################################################################

print_header "Configurando Proyecto GCP"

CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || echo "")

if [ "$CURRENT_PROJECT" != "$GCP_PROJECT" ]; then
    print_info "Configurando proyecto: $GCP_PROJECT"
    gcloud config set project "$GCP_PROJECT"
    print_success "Proyecto configurado: $GCP_PROJECT"
else
    print_success "Proyecto ya configurado: $GCP_PROJECT"
fi

###############################################################################
# Verificar permisos
###############################################################################

print_header "Verificando Permisos"

print_info "Verificando acceso a Storage..."

if gcloud storage buckets list --project="$GCP_PROJECT" &>/dev/null; then
    print_success "Tienes acceso a Google Cloud Storage"

    # Listar buckets
    BUCKET_COUNT=$(gcloud storage buckets list --project="$GCP_PROJECT" --format="value(name)" | wc -l)
    print_info "Buckets disponibles: $BUCKET_COUNT"
else
    print_warning "No tienes acceso a Storage o no hay buckets"
    print_info "Si necesitas acceso, contacta al administrador del proyecto"
fi

###############################################################################
# Test de credenciales
###############################################################################

print_header "Probando Credenciales"

print_info "Obteniendo access token..."

if gcloud auth application-default print-access-token &>/dev/null; then
    print_success "ADC funciona correctamente"
else
    print_error "Error al obtener access token"
    exit 1
fi

###############################################################################
# Resumen
###############################################################################

print_header "✅ Configuración Completada"

echo "Configuración de autenticación GCP:"
echo ""
echo "  Usuario:  $CURRENT_ACCOUNT"
echo "  Proyecto: $GCP_PROJECT"
echo "  ADC File: $ADC_FILE"
echo ""
print_success "Autenticación moderna configurada correctamente"
echo ""
print_info "Próximos pasos:"
echo "  1. Levantar servicios: cd services/vectordb && docker compose up -d"
echo "  2. Verificar logs: docker logs vectordb-api-1"
echo "  3. Test de GCS: docker exec vectordb-api-1 python -c 'from google.cloud import storage; print(storage.Client())'"
echo ""
