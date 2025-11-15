# 🚀 AURA360 - Quickstart de Deployment

**Para desplegar rápidamente a Google Cloud Platform**

---

## ⚡ Despliegue en 3 Pasos

### 1️⃣ Configurar Credenciales (15-30 min)

```bash
# Ejecutar asistente interactivo
./scripts/setup_env_production.sh
```

El script te pedirá:
- 🔐 Credenciales de Supabase
- 📡 API Keys de Confluent Cloud (Kafka)
- 🔴 URL de Redis (Upstash)
- 📊 Credenciales de Qdrant Cloud
- 🤖 Google Gemini API Key

**Resultado:** Archivos `.env.production` listos en cada servicio.

---

### 2️⃣ Desplegar Servicios (30-45 min)

```bash
# Configurar variables
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export API_ENV_FILE="services/api/.env.production"
export WORKER_ENV_FILE="services/api/.env.production"
export WEB_BUCKET="aura360-web-prod"

# Desplegar todo
./deploy_all_gcloud.sh
# Selecciona: 1 (Todos)
```

El script desplegará:
- 📦 API Django → Cloud Run
- ⚙️ Worker Celery → Cloud Run
- 🌐 Frontend Angular → Cloud Storage

---

### 3️⃣ Verificar Despliegue (5-10 min)

```bash
# Ver estado de servicios
./scripts/verify_deployments.sh

# Ejecutar pruebas E2E
./scripts/test_deployments_e2e.sh
```

**¿Todo verde?** ✅ ¡Deployment exitoso!

**¿Hay errores?** 🔴 Ver sección de [Troubleshooting](#-troubleshooting-rápido)

---

## 📋 Checklist Rápido

Antes de empezar:

### Pre-requisitos
- [ ] `gcloud` CLI instalado
- [ ] Autenticado en GCP: `gcloud auth login`
- [ ] Proyecto configurado: `gcloud config set project aura-360-471711`
- [ ] Tienes acceso a todas las consolas de servicios externos

### Credenciales Necesarias
- [ ] Supabase Database (host, user, password)
- [ ] Supabase API (service_role_key, jwt_secret)
- [ ] Kafka Bootstrap Servers + API Key/Secret
- [ ] Redis URL (Upstash)
- [ ] Qdrant URL + API Key
- [ ] Google Gemini API Key

---

## 🔄 Actualizar Despliegue Existente

### Opción 1: Re-desplegar Todo
```bash
./deploy_all_gcloud.sh
```

### Opción 2: Desplegar Servicio Específico
```bash
# Solo API
./scripts/deploy_api_gcloud.sh

# Solo Worker
./scripts/deploy_worker_gcloud.sh

# Solo Frontend
./scripts/deploy_web_gcloud.sh
```

---

## 🔍 Comandos de Verificación Rápida

```bash
# Estado general
./scripts/verify_deployments.sh

# Pruebas E2E
./scripts/test_deployments_e2e.sh

# Health check manual de API
curl $(gcloud run services describe aura360-api \
    --project aura-360-471711 \
    --region us-central1 \
    --format 'value(status.url)')/api/v1/health

# Ver logs en vivo
gcloud logging tail \
    "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-api" \
    --project aura-360-471711
```

---

## 🐛 Troubleshooting Rápido

### Error: "Service not found"
**Solución:** El servicio no está desplegado
```bash
./scripts/deploy_api_gcloud.sh  # O el servicio que falte
```

### Error: "Database connection refused"
**Causa:** Credenciales incorrectas en `.env.production`
**Solución:**
1. Verifica `DB_USER`, `DB_PASSWORD`, `DB_HOST` en Supabase Dashboard
2. Asegúrate de usar puerto `6543` (pooler)
3. Re-despliega: `./scripts/deploy_api_gcloud.sh`

### Error: "Kafka connection failed"
**Causa:** Credenciales de Kafka incorrectas
**Solución:**
1. Verifica en Confluent Cloud Console
2. Asegúrate que el formato sea: `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`
3. Verifica que las API Keys tengan permisos
4. Re-despliega: `./scripts/deploy_api_gcloud.sh`

### Error: "Health check failed"
**Diagnóstico:**
```bash
# Ver logs recientes
gcloud logging read \
    "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-api" \
    --project aura-360-471711 \
    --limit 50
```

### Error: "Module not found" en build
**Causa:** Problema con dependencias
**Solución:**
1. Verifica que `pyproject.toml` esté actualizado
2. Limpia cache de Cloud Build
3. Re-despliega forzando rebuild

---

## 📊 URLs Después del Despliegue

Ejecuta para obtener las URLs:

```bash
# API
gcloud run services describe aura360-api \
    --project aura-360-471711 \
    --region us-central1 \
    --format 'value(status.url)'

# Worker (privado)
gcloud run services describe aura360-celery \
    --project aura-360-471711 \
    --region us-central1 \
    --format 'value(status.url)'

# Frontend
echo "https://storage.googleapis.com/aura360-web-prod/index.html"
```

---

## 🎯 Post-Deployment

### Paso 1: Actualizar URLs Cruzadas

Después del primer deploy, actualiza en `services/api/.env.production`:

```bash
# Obtener URLs
API_URL=$(gcloud run services describe aura360-api \
    --project aura-360-471711 --region us-central1 \
    --format 'value(status.url)')

# Actualizar .env.production
ALLOWED_HOSTS=${API_URL#https://}
VECTOR_DB_BASE_URL=https://...  # URL de vectordb
HOLISTIC_AGENT_SERVICE_URL=https://.../api/holistic/v1/run  # URL de agents
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com/aura360-web-prod
```

### Paso 2: Re-desplegar con URLs Actualizadas

```bash
./scripts/deploy_api_gcloud.sh
```

### Paso 3: Verificar Conectividad

```bash
./scripts/test_deployments_e2e.sh
```

---

## 💡 Tips y Mejores Prácticas

### Seguridad
- ⚠️ **NUNCA** commits `.env.production` a Git
- 🔐 Rota credenciales cada 90 días
- 🛡️ Habilita Row Level Security en Supabase
- 🔑 Considera usar Secret Manager de GCP para producción

### Monitoreo
- 📊 Configura alertas en Cloud Monitoring
- 📝 Revisa logs regularmente
- 💰 Monitorea costos en GCP Console
- ✅ Ejecuta `verify_deployments.sh` semanalmente

### Performance
- 🚀 Configura VPC Connector para comunicación privada
- 🌐 Habilita Cloud CDN para el frontend
- 📈 Ajusta min/max instances según tráfico
- 💾 Usa cache de Redis efectivamente

### Costos
- 💵 Start: ~$75-95/mes (MVP, <100 usuarios)
- 💵 Growth: ~$120-140/mes (100-1K usuarios)
- 📉 Optimiza instance counts para reducir costos
- 🎁 Aprovecha free tier de Confluent Cloud (1 año)

---

## 📚 Documentación Completa

Para más detalles, consulta:

- [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) - Checklist detallado paso a paso
- [DEPLOYMENT_STATUS.md](./DEPLOYMENT_STATUS.md) - Estado actual y plan completo
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Guía completa de deployment
- [scripts/README.md](./scripts/README.md) - Documentación de scripts

---

## 🆘 Ayuda

### Verificar Estado Actual
```bash
./scripts/verify_deployments.sh
```

### Ejecutar Pruebas
```bash
./scripts/test_deployments_e2e.sh
```

### Ver Logs
```bash
# Logs de API
gcloud logging tail \
    "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-api" \
    --project aura-360-471711

# Logs de Worker
gcloud logging tail \
    "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-celery" \
    --project aura-360-471711
```

### Rollback
```bash
# Ver revisiones anteriores
gcloud run revisions list \
    --service aura360-api \
    --project aura-360-471711 \
    --region us-central1

# Rollback a revisión específica
gcloud run services update-traffic aura360-api \
    --to-revisions REVISION_NAME=100 \
    --project aura-360-471711 \
    --region us-central1
```

---

## 🎉 ¡Listo!

Una vez completado:
- ✅ Servicios desplegados y saludables
- ✅ Frontend accesible
- ✅ Health checks pasando
- ✅ Pruebas E2E sin errores

**¡Tu aplicación AURA360 está en producción! 🚀**

---

**Última actualización:** Noviembre 13, 2025  
**Tiempo estimado total:** 1-2 horas  
**Dificultad:** Intermedia

