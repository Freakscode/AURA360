# Configuración de .env.production para GCP

Este documento explica cómo configurar el archivo `.env.production` para desplegar la aplicación en Google Cloud Platform.

## 📋 Pasos para Configurar

### 1. Crear el archivo .env.production

```bash
cd services/api
cp .env.production.template .env.production
```

O crea el archivo manualmente con el siguiente contenido:

```bash
# ==============================================================================
# DJANGO CORE CONFIGURATION
# ==============================================================================
SECRET_KEY=<GENERA_UNA_SECRET_KEY_SEGURA>
DEBUG=False
ALLOWED_HOSTS=*.run.app

# ==============================================================================
# DATABASE CONFIGURATION (Supabase PostgreSQL)
# ==============================================================================
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres.<TU_PROJECT_REF>
DB_PASSWORD=<TU_DB_PASSWORD>
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=6543
CONN_MAX_AGE=600

# ==============================================================================
# SUPABASE CONFIGURATION
# ==============================================================================
SUPABASE_URL=https://<TU_PROJECT_REF>.supabase.co
SUPABASE_API_URL=https://<TU_PROJECT_REF>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<TU_SERVICE_ROLE_KEY>
SUPABASE_JWKS_URL=https://<TU_PROJECT_REF>.supabase.co/auth/v1/.well-known/jwks.json
SUPABASE_JWT_SECRET=<TU_JWT_SECRET>
SUPABASE_ADMIN_TIMEOUT=10

# ==============================================================================
# KAFKA / CONFLUENT CLOUD CONFIGURATION
# ==============================================================================
KAFKA_BOOTSTRAP_SERVERS=<pkc-xxxxx.us-east-1.aws.confluent.cloud:9092>
KAFKA_API_KEY=<TU_KAFKA_API_KEY>
KAFKA_API_SECRET=<TU_KAFKA_API_SECRET>

# ==============================================================================
# CELERY / REDIS CONFIGURATION
# ==============================================================================
CELERY_BROKER_URL=rediss://default:<PASSWORD>@<redis-host>:6379/0
CELERY_RESULT_BACKEND=rediss://default:<PASSWORD>@<redis-host>:6379/1
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=540
CELERY_TASK_DEFAULT_QUEUE=api_default

# ==============================================================================
# EXTERNAL SERVICES CONFIGURATION
# ==============================================================================
VECTOR_DB_BASE_URL=https://<vectordb-service-url>
HOLISTIC_AGENT_SERVICE_URL=https://<agents-service-url>/api/holistic/v1/run
HOLISTIC_AGENT_REQUEST_TIMEOUT=120

# ==============================================================================
# CORS CONFIGURATION
# ==============================================================================
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com
```

### 2. Obtener Credenciales de Supabase

1. **SECRET_KEY de Django**:
   ```bash
   python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
   ```

2. **Credenciales de Base de Datos**:
   - Ve a: Supabase Dashboard > Settings > Database
   - En "Connection string" > "Connection pooling", copia:
     - Host: `aws-0-us-east-1.pooler.supabase.com`
     - Port: `6543`
     - Database: `postgres`
     - User: `postgres.xxxxxx`
     - Password: Si no la tienes, haz clic en "Reset database password"

3. **Credenciales de Supabase API**:
   - Ve a: Supabase Dashboard > Settings > API
   - Copia:
     - Project URL: `https://xxxxx.supabase.co`
     - service_role key: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
     - JWT Secret: En la misma página

### 3. Obtener Credenciales de Confluent Cloud (Kafka)

1. Ve a: https://confluent.cloud/environments
2. Selecciona tu environment y cluster
3. **Bootstrap Servers**:
   - Ve a: Cluster > Settings > Cluster settings
   - Copia el valor de "Bootstrap server": `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`

4. **API Keys**:
   - Ve a: Cluster > API Keys > Add key
   - Selecciona "Cluster-specific"
   - Scope: "All topics"
   - **⚠️ IMPORTANTE**: Guarda inmediatamente el API Secret, no podrás verlo después

### 4. Configurar Redis (Celery)

**Opción A: Upstash Redis (Recomendado para empezar)**

1. Ve a: https://upstash.com
2. Crea una base de datos Redis
3. Configuración:
   - Region: `us-east-1` (mismo que otros servicios)
   - TLS: Enabled (obligatorio)
4. Copia la URL: `rediss://default:PASSWORD@HOST:6379`
5. Usa DB 0 para broker y DB 1 para result backend

**Opción B: GCP MemoryStore**

1. Ve a: GCP Console > Memorystore > Redis
2. Crea una instancia Redis
3. Configura VPC connector en Cloud Run
4. URL formato: `redis://HOST:6379`

### 5. Validar Configuración

```bash
./services/api/scripts/validate_production_env.sh services/api/.env.production
```

Este script verificará que todas las variables críticas estén configuradas.

### 6. Desplegar

```bash
export API_ENV_FILE="services/api/.env.production"
export WORKER_ENV_FILE="services/api/.env.production"
./deploy_all_gcloud.sh
```

## 🔄 Actualizaciones Post-Deploy

Después del primer deploy, necesitarás actualizar algunas URLs:

### 1. Actualizar ALLOWED_HOSTS

Obtén la URL del servicio API desde Cloud Run:
```bash
gcloud run services describe aura360-api \
  --project aura-360-471711 \
  --region us-central1 \
  --format 'value(status.url)'
```

Actualiza en `.env.production`:
```
ALLOWED_HOSTS=aura360-api-xxxxx-uc.a.run.app
```

### 2. Actualizar CORS_ALLOWED_ORIGINS

Después de desplegar el frontend, actualiza:
```
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com,https://tu-dominio.com
```

### 3. Actualizar URLs de Servicios Externos

Después de desplegar vectordb y agents:
```
VECTOR_DB_BASE_URL=https://vectordb-xxxxx-uc.a.run.app
HOLISTIC_AGENT_SERVICE_URL=https://agents-xxxxx-uc.a.run.app/api/holistic/v1/run
```

Luego re-despliega:
```bash
./deploy_all_gcloud.sh
```

## 🔒 Seguridad

- ✅ **NUNCA** commitees `.env.production` a Git (ya está en `.gitignore`)
- ✅ Usa diferentes proyectos de Supabase para dev/staging/prod
- ✅ Rota las credenciales periódicamente (cada 90 días)
- ✅ Habilita Row Level Security (RLS) en Supabase
- ✅ Usa secretos de GCP Secret Manager para valores sensibles (opcional)

## ❓ Troubleshooting

### Error: "Database connection refused"
- Verifica que `DB_PORT=6543` (pooler) o `5432` (directo)
- Verifica que `DB_HOST` use el pooler para producción

### Error: "Kafka connection failed"
- Verifica que `KAFKA_BOOTSTRAP_SERVERS` tenga el formato correcto
- Verifica que las API keys tengan permisos en el cluster

### Error: "Redis connection failed"
- Para Upstash, asegúrate de usar `rediss://` (con TLS)
- Verifica que la URL incluya la contraseña

### Error: "JWKS URL not found"
- Verifica que la URL sea exactamente: `https://TU_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json`
- Prueba accediendo a la URL en el navegador, debe devolver un JSON

## 📚 Referencias

- [PRODUCTION_ENV_SETUP.md](../../PRODUCTION_ENV_SETUP.md) - Guía detallada paso a paso
- [DEPLOYMENT_GCLOUD.md](../../docs/DEPLOYMENT_GCLOUD.md) - Documentación de despliegue
- [Supabase Docs](https://supabase.com/docs)
- [Confluent Cloud Docs](https://docs.confluent.io/cloud/current/get-started/index.html)

