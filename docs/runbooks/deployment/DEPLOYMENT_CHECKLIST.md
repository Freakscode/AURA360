# 📋 AURA360 - Checklist de Despliegue a Google Cloud

Este documento te guiará paso a paso para desplegar AURA360 a Google Cloud Platform.

## Estado Actual del Despliegue

Para verificar el estado actual, ejecuta:
```bash
./scripts/verify_deployments.sh
```

## ✅ Pre-requisitos

### 1. Herramientas Instaladas
- [ ] `gcloud` CLI instalado y configurado
- [ ] `gsutil` disponible (viene con gcloud)
- [ ] `curl` para health checks
- [ ] `jq` para parsear JSON (opcional pero útil)

### 2. Cuentas y Servicios Externos
- [ ] Cuenta de Supabase configurada
- [ ] Cuenta de Confluent Cloud (Kafka) con cluster creado
- [ ] Cuenta de Upstash (Redis) con instancia creada
- [ ] Cuenta de Qdrant Cloud con cluster creado
- [ ] API Key de Google Gemini

### 3. Verificar Autenticación GCP
```bash
gcloud auth list
gcloud config get-value project
# Debe mostrar: aura-360-471711
```

Si no está configurado:
```bash
gcloud auth login
gcloud config set project aura-360-471711
```

## 📝 Fase 1: Configuración de Variables de Entorno

### 1.1 API Django

```bash
cd services/api
cp .env.production.template .env.production
```

Edita `services/api/.env.production` y completa:

**Prioridad ALTA (sin estos, no funciona):**
- [ ] `SECRET_KEY` - Genera con: `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`
- [ ] `DB_USER`, `DB_PASSWORD`, `DB_HOST` - De Supabase Dashboard > Settings > Database
- [ ] `SUPABASE_SERVICE_ROLE_KEY` - De Supabase Dashboard > Settings > API
- [ ] `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_API_KEY`, `KAFKA_API_SECRET` - De Confluent Cloud
- [ ] `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` - De Upstash Redis

**Prioridad MEDIA (se pueden configurar después del primer deploy):**
- [ ] `VECTOR_DB_BASE_URL` - URL del servicio vectordb (después de desplegarlo)
- [ ] `HOLISTIC_AGENT_SERVICE_URL` - URL del servicio agents (después de desplegarlo)
- [ ] `ALLOWED_HOSTS` - URL del servicio API (después de desplegarlo)
- [ ] `CORS_ALLOWED_ORIGINS` - URLs permitidas

### 1.2 Agents Service

```bash
cd services/agents
# Verificar si existe .env.production o crear uno
```

Completa:
- [ ] `GOOGLE_API_KEY` - API key de Google Gemini
- [ ] `AGENT_SERVICE_QDRANT_URL` - URL de Qdrant Cloud
- [ ] `AGENT_SERVICE_QDRANT_API_KEY` - API key de Qdrant
- [ ] `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_API_KEY`, `KAFKA_API_SECRET` - Same as API

### 1.3 VectorDB Service

```bash
cd services/vectordb
# Verificar si existe .env.production o crear uno
```

Completa:
- [ ] `QDRANT_URL` - URL de Qdrant Cloud
- [ ] `QDRANT_API_KEY` - API key de Qdrant
- [ ] `REDIS_URL` - De Upstash
- [ ] `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_API_KEY`, `KAFKA_API_SECRET` - Same as API

### 1.4 Validar Configuración

```bash
# Validar que los archivos existen
./services/api/scripts/validate_production_env.sh services/api/.env.production
```

## 🚀 Fase 2: Despliegue de Servicios

### 2.1 Configurar Variables de Shell

```bash
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export API_ENV_FILE="services/api/.env.production"
export WORKER_ENV_FILE="services/api/.env.production"
export WEB_BUCKET="aura360-web-prod"
```

### 2.2 Opción A: Desplegar Todo

```bash
./deploy_all_gcloud.sh
# Selecciona: 1 (Todos)
```

### 2.2 Opción B: Desplegar Servicios Individuales

#### 2.2.1 API Django
```bash
./scripts/deploy_api_gcloud.sh
```

#### 2.2.2 Worker Celery
```bash
./scripts/deploy_worker_gcloud.sh
```

#### 2.2.3 Web Frontend
```bash
./scripts/deploy_web_gcloud.sh
```

## 🔄 Fase 3: Actualización Post-Deploy

Después del primer deploy, necesitas actualizar las URLs:

### 3.1 Obtener URLs de los Servicios

```bash
# API
API_URL=$(gcloud run services describe aura360-api \
    --project aura-360-471711 \
    --region us-central1 \
    --format 'value(status.url)')
echo "API URL: $API_URL"

# Agents
AGENTS_URL=$(gcloud run services describe aura360-agents \
    --project aura-360-471711 \
    --region us-central1 \
    --format 'value(status.url)')
echo "Agents URL: $AGENTS_URL"

# VectorDB
VECTORDB_URL=$(gcloud run services describe aura360-vectordb \
    --project aura-360-471711 \
    --region us-central1 \
    --format 'value(status.url)')
echo "VectorDB URL: $VECTORDB_URL"
```

### 3.2 Actualizar .env.production

Edita `services/api/.env.production`:

```bash
# Actualizar con las URLs reales
ALLOWED_HOSTS=aura360-api-XXXXX-uc.a.run.app
VECTOR_DB_BASE_URL=https://aura360-vectordb-XXXXX-uc.a.run.app
HOLISTIC_AGENT_SERVICE_URL=https://aura360-agents-XXXXX-uc.a.run.app/api/holistic/v1/run
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com/aura360-web-prod
```

### 3.3 Re-desplegar con URLs Actualizadas

```bash
./scripts/deploy_api_gcloud.sh
```

## ✅ Fase 4: Verificación

### 4.1 Verificar Estado de Servicios

```bash
./scripts/verify_deployments.sh
```

### 4.2 Ejecutar Pruebas E2E

```bash
./scripts/test_deployments_e2e.sh
```

### 4.3 Health Checks Manuales

```bash
# API
curl $API_URL/api/v1/health
# Esperado: {"status":"ok"}

# Agents
curl $AGENTS_URL/readyz
# Esperado: {"status":"ok"}

# VectorDB
curl $VECTORDB_URL/readyz
# Esperado: {"status":"ok"}

# Web
curl -I https://storage.googleapis.com/aura360-web-prod/index.html
# Esperado: HTTP/1.1 200 OK
```

## 📊 Fase 5: Monitoreo

### 5.1 Ver Logs en Tiempo Real

```bash
# API logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-api" \
    --project aura-360-471711

# Worker logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-celery" \
    --project aura-360-471711
```

### 5.2 Verificar Métricas

Visita:
- https://console.cloud.google.com/run?project=aura-360-471711
- https://console.cloud.google.com/logs?project=aura-360-471711

## 🐛 Troubleshooting

### Error: "Service aura360-api not found"
- Significa que el servicio no está desplegado aún
- Ejecuta: `./scripts/deploy_api_gcloud.sh`

### Error: "Database connection refused"
- Verifica `DB_HOST`, `DB_PORT`, `DB_PASSWORD` en `.env.production`
- Verifica que Supabase esté accesible

### Error: "Kafka connection failed"
- Verifica `KAFKA_BOOTSTRAP_SERVERS`, `KAFKA_API_KEY`, `KAFKA_API_SECRET`
- Verifica que el cluster de Confluent esté activo

### Error: "Health check failed"
- Revisa los logs: `gcloud logging tail ...`
- Verifica que todas las variables de entorno estén configuradas

### Error: "Module not found"
- Puede ser un problema con las dependencias
- Verifica que `pyproject.toml` tenga todas las dependencias

## 📞 Comandos Útiles

```bash
# Listar todos los servicios
gcloud run services list --project aura-360-471711 --region us-central1

# Describir un servicio
gcloud run services describe aura360-api --project aura-360-471711 --region us-central1

# Ver revisiones de un servicio
gcloud run revisions list --service aura360-api --project aura-360-471711 --region us-central1

# Rollback a una revisión anterior
gcloud run services update-traffic aura360-api --to-revisions REVISION_NAME=100 --project aura-360-471711 --region us-central1

# Eliminar un servicio
gcloud run services delete aura360-api --project aura-360-471711 --region us-central1
```

## 🎉 Finalización

Una vez completados todos los pasos:

- [ ] Todos los health checks pasan
- [ ] Las pruebas E2E pasan
- [ ] La aplicación web carga correctamente
- [ ] Los logs no muestran errores críticos

¡Deployment completado! 🚀

## 📚 Referencias

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Guía completa de deployment
- [DEPLOYMENT_GCLOUD.md](./docs/DEPLOYMENT_GCLOUD.md) - Detalles de GCloud
- [ENV_PRODUCTION_SETUP.md](./services/api/ENV_PRODUCTION_SETUP.md) - Setup de variables

