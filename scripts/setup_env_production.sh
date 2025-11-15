#!/usr/bin/env bash
# Script interactivo para configurar archivos .env.production
set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'
BOLD='\033[1m'

echo ""
echo "=========================================="
echo "  🔧 AURA360 - Configuración de Entorno"
echo "=========================================="
echo ""
echo "Este script te ayudará a configurar los archivos .env.production"
echo "para los servicios de AURA360."
echo ""

# Función para solicitar input con valor por defecto
ask() {
    local prompt="$1"
    local default="${2:-}"
    local var_name="$3"
    
    if [ -n "$default" ]; then
        read -p "${prompt} [${default}]: " value
        value="${value:-$default}"
    else
        read -p "${prompt}: " value
    fi
    
    eval "$var_name='$value'"
}

# Función para solicitar input sensible (oculta el input)
ask_secret() {
    local prompt="$1"
    local var_name="$2"
    
    read -s -p "${prompt}: " value
    echo ""
    eval "$var_name='$value'"
}

# Función para confirmar si continuar
confirm() {
    local prompt="$1"
    read -p "${prompt} (y/n): " response
    [[ "$response" =~ ^[Yy]$ ]]
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Paso 1: Configuración de API Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if confirm "¿Deseas configurar el servicio API?"; then
    echo ""
    echo "Django Core Configuration:"
    echo "──────────────────────────"
    
    # Generar SECRET_KEY automáticamente
    echo "Generando SECRET_KEY de Django..."
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || echo "CHANGE_ME")
    echo -e "${GREEN}✓ SECRET_KEY generado${NC}"
    
    ask "ALLOWED_HOSTS (separados por coma)" "*.run.app" ALLOWED_HOSTS
    
    echo ""
    echo "Supabase Configuration:"
    echo "──────────────────────────"
    echo "Obtén estos valores de: Supabase Dashboard > Settings"
    echo ""
    
    ask "Project Ref (ej: abcdefghijk)" "" SUPABASE_REF
    ask "Database User" "postgres.${SUPABASE_REF}" DB_USER
    ask_secret "Database Password" DB_PASSWORD
    ask "Database Host" "aws-0-us-east-1.pooler.supabase.com" DB_HOST
    ask "Database Port" "6543" DB_PORT
    
    SUPABASE_URL="https://${SUPABASE_REF}.supabase.co"
    SUPABASE_JWKS_URL="${SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    
    ask_secret "Supabase Service Role Key" SUPABASE_SERVICE_ROLE_KEY
    ask_secret "Supabase JWT Secret" SUPABASE_JWT_SECRET
    
    echo ""
    echo "Kafka / Confluent Cloud Configuration:"
    echo "──────────────────────────────────────"
    echo "Obtén estos valores de: Confluent Cloud Console"
    echo ""
    
    ask "Kafka Bootstrap Servers" "pkc-xxxxx.us-east-1.aws.confluent.cloud:9092" KAFKA_BOOTSTRAP_SERVERS
    ask_secret "Kafka API Key" KAFKA_API_KEY
    ask_secret "Kafka API Secret" KAFKA_API_SECRET
    
    echo ""
    echo "Redis / Upstash Configuration:"
    echo "─────────────────────────────"
    echo "Obtén estos valores de: Upstash Console"
    echo ""
    
    ask "Redis URL (formato: rediss://default:PASSWORD@HOST:6379)" "" REDIS_URL
    CELERY_BROKER_URL="${REDIS_URL}/0"
    CELERY_RESULT_BACKEND="${REDIS_URL}/1"
    
    echo ""
    echo "External Services (se pueden dejar vacíos y actualizar después):"
    echo "─────────────────────────────────────────────────────────────────"
    
    ask "Vector DB Base URL" "https://vectordb-service-url" VECTOR_DB_BASE_URL
    ask "Holistic Agent Service URL" "https://agents-service-url/api/holistic/v1/run" HOLISTIC_AGENT_SERVICE_URL
    
    echo ""
    echo "Generando archivo services/api/.env.production..."
    
    cat > services/api/.env.production <<EOF
# ==============================================================================
# DJANGO CORE CONFIGURATION
# ==============================================================================
SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${ALLOWED_HOSTS}

# ==============================================================================
# DATABASE CONFIGURATION (Supabase PostgreSQL)
# ==============================================================================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
CONN_MAX_AGE=600

# ==============================================================================
# SUPABASE CONFIGURATION
# ==============================================================================
SUPABASE_URL=${SUPABASE_URL}
SUPABASE_API_URL=${SUPABASE_URL}
SUPABASE_SERVICE_ROLE_KEY=${SUPABASE_SERVICE_ROLE_KEY}
SUPABASE_JWKS_URL=${SUPABASE_JWKS_URL}
SUPABASE_JWT_SECRET=${SUPABASE_JWT_SECRET}
SUPABASE_ADMIN_TIMEOUT=10

# ==============================================================================
# KAFKA / CONFLUENT CLOUD CONFIGURATION
# ==============================================================================
KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS}
KAFKA_API_KEY=${KAFKA_API_KEY}
KAFKA_API_SECRET=${KAFKA_API_SECRET}

# ==============================================================================
# CELERY / REDIS CONFIGURATION
# ==============================================================================
CELERY_BROKER_URL=${CELERY_BROKER_URL}
CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=540
CELERY_TASK_DEFAULT_QUEUE=api_default

# ==============================================================================
# EXTERNAL SERVICES CONFIGURATION
# ==============================================================================
VECTOR_DB_BASE_URL=${VECTOR_DB_BASE_URL}
HOLISTIC_AGENT_SERVICE_URL=${HOLISTIC_AGENT_SERVICE_URL}
HOLISTIC_AGENT_REQUEST_TIMEOUT=120

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com
EOF
    
    echo -e "${GREEN}✓ Archivo services/api/.env.production creado${NC}"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Paso 2: Configuración de Agents Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if confirm "¿Deseas configurar el servicio Agents?"; then
    echo ""
    echo "Google Gemini Configuration:"
    echo "───────────────────────────"
    
    ask_secret "Google API Key" GOOGLE_API_KEY
    
    echo ""
    echo "Qdrant Cloud Configuration:"
    echo "──────────────────────────"
    
    ask "Qdrant URL (ej: https://xxx.us-east-1.aws.cloud.qdrant.io:6333)" "" QDRANT_URL
    ask_secret "Qdrant API Key" QDRANT_API_KEY
    
    echo ""
    echo "Generando archivo services/agents/.env.production..."
    
    cat > services/agents/.env.production <<EOF
# ==============================================================================
# GOOGLE GEMINI CONFIGURATION
# ==============================================================================
GOOGLE_API_KEY=${GOOGLE_API_KEY}

# ==============================================================================
# QDRANT CLOUD CONFIGURATION
# ==============================================================================
AGENT_SERVICE_QDRANT_URL=${QDRANT_URL}
AGENT_SERVICE_QDRANT_API_KEY=${QDRANT_API_KEY}
AGENT_SERVICE_VECTOR_COLLECTION=holistic_memory
AGENT_SERVICE_VECTOR_VERIFY_SSL=true
AGENT_SERVICE_VECTOR_TOP_K=5
AGENT_SERVICE_VECTOR_RETRIES=2

# ==============================================================================
# EMBEDDING CONFIGURATION
# ==============================================================================
AGENT_DEFAULT_EMBEDDING_MODEL=models/text-embedding-004
AGENT_SERVICE_EMBEDDING_BACKEND=gemini
AGENT_SERVICE_EMBEDDING_NORMALIZE=true

# ==============================================================================
# KAFKA CONFIGURATION
# ==============================================================================
KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-}
KAFKA_API_KEY=${KAFKA_API_KEY:-}
KAFKA_API_SECRET=${KAFKA_API_SECRET:-}

# ==============================================================================
# SERVICE CONFIGURATION
# ==============================================================================
AGENT_SERVICE_TIMEOUT=30
AGENT_SERVICE_MODEL_VERSION=1.0.0
AGENT_SERVICE_RECOMMENDATION_HORIZON_DAYS=21
EOF
    
    echo -e "${GREEN}✓ Archivo services/agents/.env.production creado${NC}"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Paso 3: Configuración de VectorDB Service"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if confirm "¿Deseas configurar el servicio VectorDB?"; then
    echo ""
    echo "(Reutilizando valores de Qdrant y Redis ya configurados)"
    echo ""
    
    echo "Generando archivo services/vectordb/.env.production..."
    
    cat > services/vectordb/.env.production <<EOF
# ==============================================================================
# QDRANT CONFIGURATION
# ==============================================================================
QDRANT_URL=${QDRANT_URL:-}
QDRANT_API_KEY=${QDRANT_API_KEY:-}
PREFER_GRPC=false

# ==============================================================================
# REDIS CONFIGURATION
# ==============================================================================
REDIS_URL=${REDIS_URL:-}
BROKER_URL=${CELERY_BROKER_URL:-}
RESULT_BACKEND=${CELERY_RESULT_BACKEND:-}
CACHE_EMBEDDINGS=true
CACHE_EMBEDDING_TTL=604800

# ==============================================================================
# KAFKA CONFIGURATION
# ==============================================================================
KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-}
KAFKA_API_KEY=${KAFKA_API_KEY:-}
KAFKA_API_SECRET=${KAFKA_API_SECRET:-}

# ==============================================================================
# VECTOR CONFIGURATION
# ==============================================================================
VECTOR_COLLECTION_NAME=holistic_memory
VECTOR_DISTANCE=cosine
DEFAULT_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_VERSION=2025.10.27
EMBEDDING_DIM=384

# ==============================================================================
# TOPIC CLASSIFICATION
# ==============================================================================
AUTO_TOPICS=true
TOPIC_TOP_K=3
TOPIC_THRESHOLD=0.34
EOF
    
    echo -e "${GREEN}✓ Archivo services/vectordb/.env.production creado${NC}"
    echo ""
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Configuración Completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Archivos creados:"
[ -f services/api/.env.production ] && echo -e "  ${GREEN}✓${NC} services/api/.env.production"
[ -f services/agents/.env.production ] && echo -e "  ${GREEN}✓${NC} services/agents/.env.production"
[ -f services/vectordb/.env.production ] && echo -e "  ${GREEN}✓${NC} services/vectordb/.env.production"
echo ""
echo "Próximos pasos:"
echo "  1. Revisar y validar los archivos .env.production"
echo "  2. Ejecutar: ./deploy_all_gcloud.sh"
echo "  3. Verificar: ./scripts/verify_deployments.sh"
echo ""
echo "⚠️  IMPORTANTE:"
echo "  - NUNCA commitees archivos .env.production a Git"
echo "  - Guarda una copia segura de estos archivos"
echo "  - Después del primer deploy, actualiza las URLs de servicios"
echo ""

