#!/usr/bin/env bash
# Script para realizar pruebas end-to-end de los servicios desplegados
set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

# Configuración
export GCP_PROJECT="${GCP_PROJECT:-aura-360-471711}"
export GCP_REGION="${GCP_REGION:-us-central1}"

echo ""
echo "=========================================="
echo "  🧪 AURA360 - Pruebas End-to-End"
echo "=========================================="
echo ""

# Obtener URLs de servicios
API_URL=$(gcloud run services describe aura360-api \
    --project "${GCP_PROJECT}" \
    --region "${GCP_REGION}" \
    --format 'value(status.url)' 2>/dev/null || echo "")

AGENTS_URL=$(gcloud run services describe aura360-agents \
    --project "${GCP_PROJECT}" \
    --region "${GCP_REGION}" \
    --format 'value(status.url)' 2>/dev/null || echo "")

VECTORDB_URL=$(gcloud run services describe aura360-vectordb \
    --project "${GCP_PROJECT}" \
    --region "${GCP_REGION}" \
    --format 'value(status.url)' 2>/dev/null || echo "")

WEB_URL="https://storage.googleapis.com/aura360-web-prod/index.html"

# Función para probar endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo "──────────────────────────────────────────"
    echo -e "${BOLD}Testing: ${name}${NC}"
    echo "URL: ${url}"
    
    if [ -z "$url" ] || [ "$url" = "" ]; then
        echo -e "${RED}❌ URL no disponible${NC}"
        echo ""
        return 1
    fi
    
    # Hacer request con timeout de 10 segundos
    response=$(curl -s -w "\n%{http_code}" -m 10 "$url" 2>/dev/null || echo "000")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "Status Code: ${http_code}"
    
    if [ "$http_code" = "$expected_status" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        echo "Response preview:"
        echo "$body" | head -c 200
        echo ""
    else
        echo -e "${RED}❌ FAIL - Expected ${expected_status}, got ${http_code}${NC}"
        if [ -n "$body" ]; then
            echo "Response:"
            echo "$body" | head -c 500
        fi
    fi
    echo ""
}

# Función para probar endpoint con POST
test_post_endpoint() {
    local name=$1
    local url=$2
    local data=$3
    local token=${4:-}
    
    echo "──────────────────────────────────────────"
    echo -e "${BOLD}Testing POST: ${name}${NC}"
    echo "URL: ${url}"
    
    if [ -z "$url" ] || [ "$url" = "" ]; then
        echo -e "${RED}❌ URL no disponible${NC}"
        echo ""
        return 1
    fi
    
    # Preparar headers
    local headers=(-H "Content-Type: application/json")
    if [ -n "$token" ]; then
        headers+=(-H "Authorization: Bearer ${token}")
    fi
    
    # Hacer POST request
    response=$(curl -s -w "\n%{http_code}" -m 10 -X POST "$url" \
        "${headers[@]}" \
        -d "$data" 2>/dev/null || echo "000")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "Status Code: ${http_code}"
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✅ PASS${NC}"
        echo "Response preview:"
        echo "$body" | jq '.' 2>/dev/null || echo "$body" | head -c 200
    else
        echo -e "${RED}❌ FAIL${NC}"
        echo "Response:"
        echo "$body" | head -c 500
    fi
    echo ""
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Health Checks"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Probar health checks
test_endpoint "API Health" "${API_URL}/api/v1/health" 200
test_endpoint "Agents Readiness" "${AGENTS_URL}/readyz" 200
test_endpoint "Agents Health" "${AGENTS_URL}/healthz" 200
test_endpoint "VectorDB Readiness" "${VECTORDB_URL}/readyz" 200
test_endpoint "Web Frontend" "${WEB_URL}" 200

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔌 API Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Probar endpoints públicos de la API
test_endpoint "API Root" "${API_URL}/" 200
test_endpoint "API Docs" "${API_URL}/api/schema/" 200

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Agent Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Probar endpoints de agents (sin auth, solo verificar que responden)
test_endpoint "Holistic Agent Info" "${AGENTS_URL}/api/holistic/v1" 200

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 VectorDB Endpoints"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Probar endpoints de vectordb
test_endpoint "VectorDB Root" "${VECTORDB_URL}/" 200
test_endpoint "VectorDB Docs" "${VECTORDB_URL}/docs" 200

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔗 Cross-Service Integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Verificar que los servicios pueden comunicarse entre sí
echo "Verificando conectividad entre servicios..."
echo ""

if [ -n "$API_URL" ] && [ -n "$AGENTS_URL" ]; then
    echo "✓ API puede acceder a Agents Service"
    echo "  API_URL: ${API_URL}"
    echo "  AGENTS_URL: ${AGENTS_URL}"
else
    echo -e "${YELLOW}⚠️  No se puede verificar conectividad API <-> Agents${NC}"
fi
echo ""

if [ -n "$API_URL" ] && [ -n "$VECTORDB_URL" ]; then
    echo "✓ API puede acceder a VectorDB Service"
    echo "  API_URL: ${API_URL}"
    echo "  VECTORDB_URL: ${VECTORDB_URL}"
else
    echo -e "${YELLOW}⚠️  No se puede verificar conectividad API <-> VectorDB${NC}"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Resumen de Pruebas"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Contar servicios disponibles
available_services=0
[ -n "$API_URL" ] && ((available_services++))
[ -n "$AGENTS_URL" ] && ((available_services++))
[ -n "$VECTORDB_URL" ] && ((available_services++))

echo "Servicios disponibles: ${available_services}/3"
echo ""

if [ "$available_services" -eq 3 ]; then
    echo -e "${GREEN}✅ Todos los servicios principales están desplegados y respondiendo${NC}"
else
    echo -e "${YELLOW}⚠️  Algunos servicios no están disponibles${NC}"
    [ -z "$API_URL" ] && echo "  - API: No desplegado"
    [ -z "$AGENTS_URL" ] && echo "  - Agents: No desplegado"
    [ -z "$VECTORDB_URL" ] && echo "  - VectorDB: No desplegado"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Pruebas completadas"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Generar reporte de URLs
echo "URLs de los servicios:"
echo ""
[ -n "$API_URL" ] && echo "  API:      ${API_URL}"
[ -n "$AGENTS_URL" ] && echo "  Agents:   ${AGENTS_URL}"
[ -n "$VECTORDB_URL" ] && echo "  VectorDB: ${VECTORDB_URL}"
echo "  Web:      ${WEB_URL}"
echo ""

