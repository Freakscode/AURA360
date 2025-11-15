#!/usr/bin/env bash
# Interactive script to setup .env.production for AURA360 API
# Usage: ./setup_production_env.sh

set -euo pipefail

ENV_FILE="services/api/.env.production"
TEMP_FILE=$(mktemp)

echo "=========================================="
echo "  AURA360 - Production Environment Setup"
echo "=========================================="
echo ""
echo "Este script te ayudará a configurar $ENV_FILE"
echo ""

# Check if file exists and backup
if [[ -f "$ENV_FILE" ]]; then
    BACKUP_FILE="${ENV_FILE}.backup.$(date +%Y%m%d%H%M%S)"
    cp "$ENV_FILE" "$BACKUP_FILE"
    echo "✅ Backup creado: $BACKUP_FILE"
    echo ""
fi

# Copy template
cp "$ENV_FILE" "$TEMP_FILE"

# Helper function to update env var
update_env() {
    local key="$1"
    local value="$2"
    # Escape special characters for sed
    value_escaped=$(printf '%s\n' "$value" | sed 's/[[\.*^$()+?{|]/\\&/g')
    sed -i.bak "s|^${key}=.*|${key}=${value_escaped}|g" "$TEMP_FILE"
    rm -f "${TEMP_FILE}.bak"
}

# ============================================================================
# Django Configuration
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  Django Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Generando SECRET_KEY segura..."
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
update_env "SECRET_KEY" "$SECRET_KEY"
echo "✅ SECRET_KEY generada"
echo ""

# ============================================================================
# Supabase Configuration
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  Supabase Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ve a: https://app.supabase.com/project/YOUR_PROJECT/settings/api"
echo ""

read -p "Project URL (ej: https://abcd1234.supabase.co): " SUPABASE_URL
SUPABASE_URL=$(echo "$SUPABASE_URL" | xargs)  # Trim whitespace

if [[ -z "$SUPABASE_URL" ]]; then
    echo "⚠️  Saltando configuración de Supabase (deberás configurarlo manualmente)"
else
    update_env "SUPABASE_URL" "$SUPABASE_URL"

    # Extract project ref from URL
    PROJECT_REF=$(echo "$SUPABASE_URL" | sed -E 's|https://([^.]+)\.supabase\.co|\1|')
    JWKS_URL="${SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    update_env "SUPABASE_JWKS_URL" "$JWKS_URL"

    echo ""
    read -p "Anon/Public Key (empieza con eyJhbGci...): " SUPABASE_ANON_KEY
    if [[ -n "$SUPABASE_ANON_KEY" ]]; then
        update_env "SUPABASE_PUBLISHABLE_KEY" "$SUPABASE_ANON_KEY"
    fi

    echo ""
    read -p "Service Role Key (⚠️  SECRETA - empieza con eyJhbGci...): " SUPABASE_SERVICE_KEY
    if [[ -n "$SUPABASE_SERVICE_KEY" ]]; then
        update_env "SUPABASE_SERVICE_ROLE_KEY" "$SUPABASE_SERVICE_KEY"
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Database Credentials (Connection Pooling)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Ve a: Settings > Database > Connection string > Connection pooling"
    echo ""

    read -p "Database User (ej: postgres.$PROJECT_REF): " DB_USER
    if [[ -n "$DB_USER" ]]; then
        update_env "DB_USER" "$DB_USER"
    fi

    read -sp "Database Password: " DB_PASSWORD
    echo ""
    if [[ -n "$DB_PASSWORD" ]]; then
        update_env "DB_PASSWORD" "$DB_PASSWORD"
    fi

    read -p "Database Host (default: aws-0-us-east-1.pooler.supabase.com): " DB_HOST
    DB_HOST=${DB_HOST:-aws-0-us-east-1.pooler.supabase.com}
    update_env "DB_HOST" "$DB_HOST"

    echo "✅ Supabase configurado"
fi

echo ""

# ============================================================================
# Kafka/Confluent Cloud Configuration
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  Kafka (Confluent Cloud) Configuration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Ve a: https://confluent.cloud/environments"
echo "Cluster > Settings > Bootstrap server"
echo ""

read -p "Bootstrap Servers (ej: pkc-xxx.us-east-1.aws.confluent.cloud:9092): " KAFKA_BOOTSTRAP
if [[ -n "$KAFKA_BOOTSTRAP" ]]; then
    update_env "KAFKA_BOOTSTRAP_SERVERS" "$KAFKA_BOOTSTRAP"

    echo ""
    read -p "Kafka API Key: " KAFKA_KEY
    if [[ -n "$KAFKA_KEY" ]]; then
        update_env "KAFKA_API_KEY" "$KAFKA_KEY"
    fi

    read -sp "Kafka API Secret: " KAFKA_SECRET
    echo ""
    if [[ -n "$KAFKA_SECRET" ]]; then
        update_env "KAFKA_API_SECRET" "$KAFKA_SECRET"
    fi

    echo "✅ Kafka configurado"
else
    echo "⚠️  Saltando configuración de Kafka (deberás configurarlo manualmente)"
fi

echo ""

# ============================================================================
# Save file
# ============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Guardando configuración..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mv "$TEMP_FILE" "$ENV_FILE"
chmod 600 "$ENV_FILE"  # Secure permissions

echo ""
echo "✅ Archivo guardado: $ENV_FILE"
echo ""

# ============================================================================
# Validate
# ============================================================================
echo "Validando configuración..."
echo ""

if ./services/api/scripts/validate_production_env.sh "$ENV_FILE"; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ✅ Configuración completada"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Siguiente paso:"
    echo ""
    echo "  export API_ENV_FILE=\"$ENV_FILE\""
    echo "  export WORKER_ENV_FILE=\"$ENV_FILE\""
    echo "  ./deploy_all_gcloud.sh"
    echo ""
else
    echo ""
    echo "⚠️  Algunas variables necesitan ser configuradas manualmente"
    echo ""
    echo "Edita el archivo: $ENV_FILE"
    echo "Guía completa: PRODUCTION_ENV_SETUP.md"
    echo ""
    echo "Después de completar, ejecuta:"
    echo "  ./services/api/scripts/validate_production_env.sh"
fi
