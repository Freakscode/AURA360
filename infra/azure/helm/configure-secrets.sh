#!/bin/bash
# AURA360 - Script para configurar secrets en Kubernetes
# Este script te guía para configurar las credenciales correctamente

set -e

ENVIRONMENT="${1:-dev}"
AKS_RESOURCE_GROUP=${AKS_RESOURCE_GROUP:-"aura360-${ENVIRONMENT}-rg"}
AKS_CLUSTER_NAME=${AKS_CLUSTER_NAME:-"aura360-${ENVIRONMENT}-aks"}

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

NAMESPACE="aura360"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AURA360 - Configuración de Secrets${NC}"
echo -e "${GREEN}========================================${NC}"

# Check kubectl / az
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}kubectl no está instalado. Por favor instálalo primero.${NC}"
    exit 1
fi

if ! command -v az &> /dev/null; then
    echo -e "${RED}Azure CLI no está instalada. Instálala antes de continuar.${NC}"
    exit 1
fi

# Check AKS connection
echo -e "\n${YELLOW}Verificando conexión a AKS...${NC}"
if ! kubectl get nodes > /dev/null 2>&1; then
    echo -e "${YELLOW}Intentando descargar credenciales para ${AKS_CLUSTER_NAME}...${NC}"
    if az aks get-credentials --resource-group "${AKS_RESOURCE_GROUP}" --name "${AKS_CLUSTER_NAME}" --overwrite-existing >/dev/null; then
        kubectl get nodes > /dev/null 2>&1 || {
            echo -e "${RED}No se pudo acceder al cluster después de obtener credenciales.${NC}"
            exit 1
        }
    else
        echo -e "${RED}No se pudo conectar automáticamente al cluster AKS.${NC}"
        echo -e "${YELLOW}Ejecuta manualmente:${NC}"
        echo -e "  ${BLUE}az aks get-credentials --resource-group ${AKS_RESOURCE_GROUP} --name ${AKS_CLUSTER_NAME}${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ Conectado a AKS${NC}"

# Create namespace if not exists
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f - > /dev/null 2>&1

echo -e "\n${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${YELLOW}OPCIÓN 1: Usar credenciales locales (DESARROLLO SOLAMENTE)${NC}"
echo -e "${YELLOW}═══════════════════════════════════════${NC}"
echo -e "${RED}⚠️  ADVERTENCIA: Estas son credenciales del Supabase LOCAL${NC}"
echo -e "${RED}⚠️  NO usar en producción o con datos reales${NC}"
echo ""
echo -e "Credenciales encontradas en tu configuración local:"
echo -e "  ${BLUE}Supabase URL:${NC} http://127.0.0.1:54321 (LOCAL)"
echo -e "  ${BLUE}JWT Secret:${NC} c6e7921692a6f3ddcc754210b46d706670c19e38ff275d88c3396f53fa18f166"
echo -e "  ${BLUE}Google API Key:${NC} AIzaSyDurj7hebJLQkLqhqcDikRbg17QK1qsW64"
echo ""

read -p "¿Quieres usar las credenciales locales para testing? (s/N): " use_local
use_local=${use_local:-n}

if [[ "$use_local" =~ ^[Ss]$ ]]; then
    echo -e "\n${YELLOW}Configurando credenciales LOCALES...${NC}"

    # Supabase Local credentials
    kubectl create secret generic supabase-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=url='http://127.0.0.1:54321' \
      --from-literal=service_role_key='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU' \
      --from-literal=jwt_secret='c6e7921692a6f3ddcc754210b46d706670c19e38ff275d88c3396f53fa18f166' \
      --from-literal=anon_key='sb_publishable_ACJWlzQHlZjBrEguHvfOxg_3BJgxAaH' \
      --dry-run=client -o yaml | kubectl apply -f -

    # Google API credentials
    kubectl create secret generic google-api-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=api_key='AIzaSyDurj7hebJLQkLqhqcDikRbg17QK1qsW64' \
      --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${GREEN}✓ Secrets configurados con credenciales locales${NC}"
    echo -e "${RED}⚠️  RECUERDA: Solo para desarrollo/testing${NC}"

else
    echo -e "\n${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}OPCIÓN 2: Configurar credenciales de PRODUCCIÓN${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Necesitas obtener las credenciales de Supabase en la nube:${NC}"
    echo -e "  1. Ve a: ${GREEN}https://supabase.com/dashboard${NC}"
    echo -e "  2. Selecciona tu proyecto (o crea uno nuevo)"
    echo -e "  3. Ve a: ${GREEN}Settings → API${NC}"
    echo -e "  4. Copia los valores que se muestran"
    echo ""

    # Supabase URL
    echo -e "${YELLOW}─────────────────────────────────────${NC}"
    echo -e "${BLUE}1. SUPABASE_URL${NC}"
    echo -e "   Ejemplo: https://xxxyyyzzzz.supabase.co"
    read -p "   Ingresa tu Supabase URL: " SUPABASE_URL

    if [[ -z "$SUPABASE_URL" ]]; then
        echo -e "${RED}URL no puede estar vacía. Abortando.${NC}"
        exit 1
    fi

    # Service Role Key
    echo -e "\n${BLUE}2. SERVICE_ROLE_KEY (secret)${NC}"
    echo -e "   ${RED}⚠️  Esta es una clave secreta con permisos administrativos${NC}"
    echo -e "   Ubicación en dashboard: Settings → API → service_role (secret)"
    echo -e "   Ejemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    read -s -p "   Ingresa tu Service Role Key: " SERVICE_ROLE_KEY
    echo ""

    if [[ -z "$SERVICE_ROLE_KEY" ]]; then
        echo -e "${RED}Service Role Key no puede estar vacía. Abortando.${NC}"
        exit 1
    fi

    # JWT Secret
    echo -e "\n${BLUE}3. JWT_SECRET${NC}"
    echo -e "   Ubicación en dashboard: Settings → API → JWT Secret"
    echo -e "   Es una cadena alfanumérica larga"
    read -s -p "   Ingresa tu JWT Secret: " JWT_SECRET
    echo ""

    if [[ -z "$JWT_SECRET" ]]; then
        echo -e "${RED}JWT Secret no puede estar vacío. Abortando.${NC}"
        exit 1
    fi

    # Anon Key
    echo -e "\n${BLUE}4. ANON_KEY (public)${NC}"
    echo -e "   Ubicación en dashboard: Settings → API → anon public"
    echo -e "   Ejemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    read -s -p "   Ingresa tu Anon Key: " ANON_KEY
    echo ""

    if [[ -z "$ANON_KEY" ]]; then
        echo -e "${RED}Anon Key no puede estar vacía. Abortando.${NC}"
        exit 1
    fi

    # Google API Key
    echo -e "\n${YELLOW}─────────────────────────────────────${NC}"
    echo -e "${BLUE}5. GOOGLE_API_KEY${NC}"
    echo -e "   Para obtenerla:"
    echo -e "   1. Ve a: ${GREEN}https://console.cloud.google.com/apis/credentials${NC}"
    echo -e "   2. Crea un proyecto (si no tienes uno)"
    echo -e "   3. Click en '+ CREATE CREDENTIALS' → 'API key'"
    echo -e "   4. Habilita las APIs necesarias:"
    echo -e "      - Generative Language API"
    echo -e "      - Vertex AI API (opcional)"
    echo ""
    read -p "   ¿Quieres usar la Google API Key actual? (${YELLOW}AIza...W64${NC}) (S/n): " use_existing_google
    use_existing_google=${use_existing_google:-s}

    if [[ "$use_existing_google" =~ ^[Ss]$ ]]; then
        GOOGLE_API_KEY="AIzaSyDurj7hebJLQkLqhqcDikRbg17QK1qsW64"
        echo -e "   ${GREEN}✓ Usando Google API Key existente${NC}"
    else
        read -s -p "   Ingresa tu nueva Google API Key: " GOOGLE_API_KEY
        echo ""

        if [[ -z "$GOOGLE_API_KEY" ]]; then
            echo -e "${RED}Google API Key no puede estar vacía. Abortando.${NC}"
            exit 1
        fi
    fi

    # Confirmation
    echo -e "\n${YELLOW}─────────────────────────────────────${NC}"
    echo -e "${YELLOW}Resumen de credenciales a configurar:${NC}"
    echo -e "  ${BLUE}Supabase URL:${NC} ${SUPABASE_URL}"
    echo -e "  ${BLUE}Service Role Key:${NC} ${SERVICE_ROLE_KEY:0:20}..."
    echo -e "  ${BLUE}JWT Secret:${NC} ${JWT_SECRET:0:20}..."
    echo -e "  ${BLUE}Anon Key:${NC} ${ANON_KEY:0:20}..."
    echo -e "  ${BLUE}Google API Key:${NC} ${GOOGLE_API_KEY:0:20}..."
    echo ""

    read -p "¿Confirmas que quieres crear estos secrets en AKS? (s/N): " confirm
    confirm=${confirm:-n}

    if [[ ! "$confirm" =~ ^[Ss]$ ]]; then
        echo -e "${RED}Operación cancelada.${NC}"
        exit 0
    fi

    # Create secrets
    echo -e "\n${YELLOW}Creando secrets en Kubernetes...${NC}"

    kubectl create secret generic supabase-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=url="${SUPABASE_URL}" \
      --from-literal=service_role_key="${SERVICE_ROLE_KEY}" \
      --from-literal=jwt_secret="${JWT_SECRET}" \
      --from-literal=anon_key="${ANON_KEY}" \
      --dry-run=client -o yaml | kubectl apply -f -

    kubectl create secret generic google-api-credentials \
      --namespace ${NAMESPACE} \
      --from-literal=api_key="${GOOGLE_API_KEY}" \
      --dry-run=client -o yaml | kubectl apply -f -

    echo -e "${GREEN}✓ Secrets configurados exitosamente${NC}"
fi

echo -e "\n${YELLOW}Verificando secrets...${NC}"
kubectl get secrets -n ${NAMESPACE} | grep -E 'supabase-credentials|google-api-credentials'

echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Configuración de secrets completada${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"

echo -e "\n${YELLOW}Comandos útiles:${NC}"
echo -e "  ${BLUE}Ver secrets:${NC}"
echo -e "    kubectl get secrets -n ${NAMESPACE}"
echo -e "\n  ${BLUE}Ver contenido de un secret (base64):${NC}"
echo -e "    kubectl get secret supabase-credentials -n ${NAMESPACE} -o yaml"
echo -e "\n  ${BLUE}Decodificar un valor:${NC}"
echo -e "    kubectl get secret supabase-credentials -n ${NAMESPACE} -o jsonpath='{.data.url}' | base64 -d"
echo -e "\n  ${BLUE}Editar un secret:${NC}"
echo -e "    kubectl edit secret supabase-credentials -n ${NAMESPACE}"
echo -e "\n  ${BLUE}Eliminar secrets (para reconfigurar):${NC}"
echo -e "    kubectl delete secret supabase-credentials -n ${NAMESPACE}"
echo -e "    kubectl delete secret google-api-credentials -n ${NAMESPACE}"

echo -e "\n${GREEN}¡Listo! Ahora puedes desplegar AURA360 con:${NC}"
echo -e "  ${BLUE}cd infra/azure/helm && ./deploy.sh ${ENVIRONMENT}${NC}"
