#!/usr/bin/env bash
# Validates that all required production environment variables are set
# Usage: ./scripts/validate_production_env.sh [path/to/.env.production]

set -euo pipefail

ENV_FILE="${1:-services/api/.env.production}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ Error: $ENV_FILE no encontrado"
  exit 1
fi

echo "🔍 Validando variables de entorno en: $ENV_FILE"
echo ""

ERRORS=0

check_var() {
  local var_name="$1"
  local var_value
  var_value=$(grep "^${var_name}=" "$ENV_FILE" | cut -d'=' -f2- || echo "")

  if [[ -z "$var_value" ]]; then
    echo "❌ $var_name: NO CONFIGURADA"
    ((ERRORS++))
    return 1
  fi

  if [[ "$var_value" == *"REPLACE"* ]]; then
    echo "⚠️  $var_name: CONTIENE PLACEHOLDER (necesita ser reemplazado)"
    ((ERRORS++))
    return 1
  fi

  echo "✅ $var_name: configurada"
  return 0
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Django Core"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_var "SECRET_KEY"
check_var "DEBUG"
check_var "ALLOWED_HOSTS"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Database (Supabase PostgreSQL)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_var "DB_USER"
check_var "DB_PASSWORD"
check_var "DB_HOST"
check_var "DB_PORT"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Supabase"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_var "SUPABASE_URL"
check_var "SUPABASE_SERVICE_ROLE_KEY"
check_var "SUPABASE_JWKS_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Kafka (Confluent Cloud)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_var "KAFKA_BOOTSTRAP_SERVERS"
check_var "KAFKA_API_KEY"
check_var "KAFKA_API_SECRET"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "External Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
check_var "VECTOR_DB_BASE_URL" || echo "   ℹ️  Se configurará después del deploy"
check_var "HOLISTIC_AGENT_SERVICE_URL" || echo "   ℹ️  Se configurará después del deploy"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Resumen"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $ERRORS -eq 0 ]]; then
  echo "✅ Todas las variables críticas están configuradas"
  echo ""
  echo "Siguiente paso:"
  echo "  export API_ENV_FILE=\"$ENV_FILE\""
  echo "  ./deploy_all_gcloud.sh"
  exit 0
else
  echo "❌ $ERRORS variable(s) necesitan ser configuradas"
  echo ""
  echo "Para obtener las credenciales de Supabase:"
  echo "  1. Ve a https://app.supabase.com/project/YOUR_PROJECT_ID/settings/api"
  echo "  2. Copia los valores y actualiza $ENV_FILE"
  echo ""
  echo "Para obtener las credenciales de Kafka (Confluent Cloud):"
  echo "  1. Ve a https://confluent.cloud/environments"
  echo "  2. Selecciona tu cluster > Settings"
  echo "  3. Copia Bootstrap servers y crea un API Key"
  exit 1
fi
