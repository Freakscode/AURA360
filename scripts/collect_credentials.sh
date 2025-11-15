#!/usr/bin/env bash
# Script interactivo para recopilar y validar credenciales
set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

echo ""
echo "=========================================="
echo "  🔐 Recopilación de Credenciales"
echo "  AURA360 - Deployment a GCP"
echo "=========================================="
echo ""

# Función para abrir URL en navegador
open_url() {
    local url=$1
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open "$url"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open "$url" 2>/dev/null || echo "Abre manualmente: $url"
    else
        echo "Abre manualmente: $url"
    fi
}

# Función para preguntar sí/no
ask_yes_no() {
    local prompt=$1
    local response
    read -p "${prompt} (y/n): " response
    [[ "$response" =~ ^[Yy]$ ]]
}

echo "Esta herramienta te guiará para recopilar todas las credenciales"
echo "necesarias para desplegar AURA360 a Google Cloud Platform."
echo ""
echo "Necesitarás acceso a:"
echo "  • Supabase Dashboard"
echo "  • Confluent Cloud Console"
echo "  • Upstash Console"
echo "  • Qdrant Cloud Dashboard"
echo "  • Google AI Studio (Gemini)"
echo ""

if ! ask_yes_no "¿Estás listo para comenzar?"; then
    echo "Está bien. Cuando estés listo, ejecuta: ./scripts/collect_credentials.sh"
    exit 0
fi

# Crear archivo temporal para guardar credenciales
TEMP_CREDS="/tmp/aura360_credentials_$(date +%s).txt"
echo "# AURA360 Production Credentials - $(date)" > "$TEMP_CREDS"
echo "# ⚠️  MANTÉN ESTE ARCHIVO SEGURO Y NO LO COMMITEES A GIT" >> "$TEMP_CREDS"
echo "" >> "$TEMP_CREDS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Supabase (Database + Authentication)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ask_yes_no "¿Quieres abrir Supabase Dashboard en el navegador?"; then
    open_url "https://supabase.com/dashboard"
    echo ""
    echo "Abriendo Supabase Dashboard..."
    sleep 2
fi

echo ""
echo -e "${CYAN}Navega a: Settings → Database → Connection Pooling${NC}"
echo ""

read -p "Database Host (ej: aws-0-us-east-1.pooler.supabase.com): " DB_HOST
read -p "Database Port [6543]: " DB_PORT
DB_PORT=${DB_PORT:-6543}
read -p "Database User (ej: postgres.abcdefg): " DB_USER
read -s -p "Database Password: " DB_PASSWORD
echo ""

echo "" >> "$TEMP_CREDS"
echo "# Supabase Database" >> "$TEMP_CREDS"
echo "DB_HOST=$DB_HOST" >> "$TEMP_CREDS"
echo "DB_PORT=$DB_PORT" >> "$TEMP_CREDS"
echo "DB_USER=$DB_USER" >> "$TEMP_CREDS"
echo "DB_PASSWORD=$DB_PASSWORD" >> "$TEMP_CREDS"

echo ""
echo -e "${CYAN}Ahora navega a: Settings → API${NC}"
echo ""

read -p "Project URL (ej: https://abcdefg.supabase.co): " SUPABASE_URL
read -s -p "Service Role Key: " SUPABASE_SERVICE_ROLE_KEY
echo ""
read -s -p "JWT Secret: " SUPABASE_JWT_SECRET
echo ""

echo "" >> "$TEMP_CREDS"
echo "# Supabase API" >> "$TEMP_CREDS"
echo "SUPABASE_URL=$SUPABASE_URL" >> "$TEMP_CREDS"
echo "SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY" >> "$TEMP_CREDS"
echo "SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET" >> "$TEMP_CREDS"

echo -e "${GREEN}✓ Credenciales de Supabase guardadas${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Confluent Cloud (Apache Kafka)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ask_yes_no "¿Quieres abrir Confluent Cloud en el navegador?"; then
    open_url "https://confluent.cloud"
    echo ""
    echo "Abriendo Confluent Cloud..."
    sleep 2
fi

echo ""
echo -e "${CYAN}Navega a: Cluster → Settings${NC}"
echo ""

read -p "Bootstrap Servers (ej: pkc-xxxxx.us-east-1.aws.confluent.cloud:9092): " KAFKA_BOOTSTRAP_SERVERS

echo ""
echo -e "${CYAN}Navega a: Cluster → API Keys${NC}"
echo ""

read -p "Kafka API Key: " KAFKA_API_KEY
read -s -p "Kafka API Secret: " KAFKA_API_SECRET
echo ""

echo "" >> "$TEMP_CREDS"
echo "# Confluent Cloud (Kafka)" >> "$TEMP_CREDS"
echo "KAFKA_BOOTSTRAP_SERVERS=$KAFKA_BOOTSTRAP_SERVERS" >> "$TEMP_CREDS"
echo "KAFKA_API_KEY=$KAFKA_API_KEY" >> "$TEMP_CREDS"
echo "KAFKA_API_SECRET=$KAFKA_API_SECRET" >> "$TEMP_CREDS"

echo -e "${GREEN}✓ Credenciales de Kafka guardadas${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Upstash (Redis - Celery Broker)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ask_yes_no "¿Quieres abrir Upstash Console en el navegador?"; then
    open_url "https://console.upstash.com"
    echo ""
    echo "Abriendo Upstash Console..."
    sleep 2
fi

echo ""
echo -e "${CYAN}Selecciona tu database Redis y copia la URL${NC}"
echo -e "${YELLOW}⚠️  Debe empezar con 'rediss://' (con doble 's' para TLS)${NC}"
echo ""

read -p "Redis URL completa: " REDIS_URL

echo "" >> "$TEMP_CREDS"
echo "# Upstash Redis" >> "$TEMP_CREDS"
echo "REDIS_URL=$REDIS_URL" >> "$TEMP_CREDS"
echo "CELERY_BROKER_URL=${REDIS_URL}/0" >> "$TEMP_CREDS"
echo "CELERY_RESULT_BACKEND=${REDIS_URL}/1" >> "$TEMP_CREDS"

echo -e "${GREEN}✓ Credenciales de Redis guardadas${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  Qdrant Cloud (Vector Database)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ask_yes_no "¿Quieres abrir Qdrant Cloud en el navegador?"; then
    open_url "https://cloud.qdrant.io"
    echo ""
    echo "Abriendo Qdrant Cloud..."
    sleep 2
fi

echo ""
echo -e "${CYAN}Selecciona tu cluster y copia la URL y API Key${NC}"
echo ""

read -p "Qdrant URL (ej: https://xxx.us-east-1.aws.cloud.qdrant.io:6333): " QDRANT_URL
read -s -p "Qdrant API Key: " QDRANT_API_KEY
echo ""

echo "" >> "$TEMP_CREDS"
echo "# Qdrant Cloud" >> "$TEMP_CREDS"
echo "QDRANT_URL=$QDRANT_URL" >> "$TEMP_CREDS"
echo "QDRANT_API_KEY=$QDRANT_API_KEY" >> "$TEMP_CREDS"

echo -e "${GREEN}✓ Credenciales de Qdrant guardadas${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  Google Gemini (AI API)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if ask_yes_no "¿Quieres abrir Google AI Studio en el navegador?"; then
    open_url "https://aistudio.google.com/app/apikey"
    echo ""
    echo "Abriendo Google AI Studio..."
    sleep 2
fi

echo ""
read -s -p "Google API Key: " GOOGLE_API_KEY
echo ""

echo "" >> "$TEMP_CREDS"
echo "# Google Gemini" >> "$TEMP_CREDS"
echo "GOOGLE_API_KEY=$GOOGLE_API_KEY" >> "$TEMP_CREDS"

echo -e "${GREEN}✓ Credenciales de Google Gemini guardadas${NC}"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Recopilación Completada"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Todas las credenciales han sido recopiladas y guardadas en:"
echo -e "${CYAN}$TEMP_CREDS${NC}"
echo ""

echo "Las credenciales han sido guardadas temporalmente."
echo ""

if ask_yes_no "¿Quieres ver las credenciales recopiladas?"; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat "$TEMP_CREDS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

echo ""
echo "Próximos pasos:"
echo ""
echo "1️⃣  Crear archivos .env.production con estas credenciales:"
echo "   ${BLUE}./scripts/setup_env_production.sh${NC}"
echo ""
echo "2️⃣  O copiar manualmente las credenciales a:"
echo "   • services/api/.env.production"
echo "   • services/agents/.env.production"
echo "   • services/vectordb/.env.production"
echo ""
echo "3️⃣  Desplegar a GCP:"
echo "   ${BLUE}./deploy_all_gcloud.sh${NC}"
echo ""

if ask_yes_no "¿Quieres que te ayude a crear los archivos .env.production ahora?"; then
    echo ""
    echo "Generando archivos .env.production..."
    echo ""
    
    # Generar SECRET_KEY para Django
    SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())' 2>/dev/null || echo "CHANGE_ME_$(openssl rand -hex 32)")
    
    # Crear services/api/.env.production
    cat > services/api/.env.production <<EOF
# ==============================================================================
# DJANGO CORE CONFIGURATION
# ==============================================================================
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=*.run.app

# ==============================================================================
# DATABASE CONFIGURATION (Supabase PostgreSQL)
# ==============================================================================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
CONN_MAX_AGE=600

# ==============================================================================
# SUPABASE CONFIGURATION
# ==============================================================================
SUPABASE_URL=$SUPABASE_URL
SUPABASE_API_URL=$SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=$SUPABASE_SERVICE_ROLE_KEY
SUPABASE_JWKS_URL=${SUPABASE_URL}/auth/v1/.well-known/jwks.json
SUPABASE_JWT_SECRET=$SUPABASE_JWT_SECRET
SUPABASE_ADMIN_TIMEOUT=10

# ==============================================================================
# KAFKA / CONFLUENT CLOUD CONFIGURATION
# ==============================================================================
KAFKA_BOOTSTRAP_SERVERS=$KAFKA_BOOTSTRAP_SERVERS
KAFKA_API_KEY=$KAFKA_API_KEY
KAFKA_API_SECRET=$KAFKA_API_SECRET

# ==============================================================================
# CELERY / REDIS CONFIGURATION
# ==============================================================================
CELERY_BROKER_URL=${REDIS_URL}/0
CELERY_RESULT_BACKEND=${REDIS_URL}/1
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=540
CELERY_TASK_DEFAULT_QUEUE=api_default

# ==============================================================================
# EXTERNAL SERVICES CONFIGURATION
# ==============================================================================
VECTOR_DB_BASE_URL=https://vectordb-service-url
HOLISTIC_AGENT_SERVICE_URL=https://agents-service-url/api/holistic/v1/run
HOLISTIC_AGENT_REQUEST_TIMEOUT=120

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com
EOF
    
    echo -e "${GREEN}✓ Creado: services/api/.env.production${NC}"
    
    # Crear services/agents/.env.production
    cat > services/agents/.env.production <<EOF
# ==============================================================================
# GOOGLE GEMINI CONFIGURATION
# ==============================================================================
GOOGLE_API_KEY=$GOOGLE_API_KEY

# ==============================================================================
# QDRANT CLOUD CONFIGURATION
# ==============================================================================
AGENT_SERVICE_QDRANT_URL=$QDRANT_URL
AGENT_SERVICE_QDRANT_API_KEY=$QDRANT_API_KEY
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
KAFKA_BOOTSTRAP_SERVERS=$KAFKA_BOOTSTRAP_SERVERS
KAFKA_API_KEY=$KAFKA_API_KEY
KAFKA_API_SECRET=$KAFKA_API_SECRET

# ==============================================================================
# SERVICE CONFIGURATION
# ==============================================================================
AGENT_SERVICE_TIMEOUT=30
AGENT_SERVICE_MODEL_VERSION=1.0.0
AGENT_SERVICE_RECOMMENDATION_HORIZON_DAYS=21
EOF
    
    echo -e "${GREEN}✓ Creado: services/agents/.env.production${NC}"
    
    # Crear services/vectordb/.env.production
    cat > services/vectordb/.env.production <<EOF
# ==============================================================================
# QDRANT CONFIGURATION
# ==============================================================================
QDRANT_URL=$QDRANT_URL
QDRANT_API_KEY=$QDRANT_API_KEY
PREFER_GRPC=false

# ==============================================================================
# REDIS CONFIGURATION
# ==============================================================================
REDIS_URL=$REDIS_URL
BROKER_URL=${REDIS_URL}/0
RESULT_BACKEND=${REDIS_URL}/1
CACHE_EMBEDDINGS=true
CACHE_EMBEDDING_TTL=604800

# ==============================================================================
# KAFKA CONFIGURATION
# ==============================================================================
KAFKA_BOOTSTRAP_SERVERS=$KAFKA_BOOTSTRAP_SERVERS
KAFKA_API_KEY=$KAFKA_API_KEY
KAFKA_API_SECRET=$KAFKA_API_SECRET

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
    
    echo -e "${GREEN}✓ Creado: services/vectordb/.env.production${NC}"
    
    echo ""
    echo -e "${GREEN}✅ Todos los archivos .env.production creados exitosamente!${NC}"
    echo ""
    echo "Próximo paso: Desplegar a GCP"
    echo "  ${BLUE}./deploy_all_gcloud.sh${NC}"
    echo ""
else
    echo ""
    echo "Puedes crear los archivos .env.production manualmente usando:"
    echo "  ${BLUE}./scripts/setup_env_production.sh${NC}"
    echo ""
    echo "O copiar manualmente desde: $TEMP_CREDS"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  IMPORTANTE - Seguridad"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "• El archivo temporal será eliminado en 5 minutos"
echo "• NUNCA commitees archivos .env.production a Git"
echo "• Guarda una copia segura de las credenciales"
echo "• Los archivos .env.production ya están en .gitignore"
echo ""

# Limpiar archivo temporal después de 5 minutos
(sleep 300 && rm -f "$TEMP_CREDS" && echo "Archivo temporal eliminado por seguridad") &

echo "¡Listo para desplegar! 🚀"
echo ""

