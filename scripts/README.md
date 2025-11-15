# Scripts de AURA360

Este directorio contiene scripts de utilidad para el proyecto AURA360.

## 📄 Tabla de Contenidos

- [Scripts de Deployment](#-scripts-de-deployment)
- [Scripts de Verificación](#-scripts-de-verificación)
- [Scripts de Configuración](#-scripts-de-configuración)
- [Scripts de Testing](#-scripts-de-testing)
- [Documentación Adicional](#-documentación-adicional)

---

## 🚀 Scripts de Deployment

### `deploy_all_gcloud.sh` (Principal)

Script maestro para desplegar todos los servicios de AURA360 a Google Cloud.

**Ubicación**: Raíz del proyecto (`./deploy_all_gcloud.sh`)

**Uso**:
```bash
export GCP_PROJECT="aura-360-471711"
export GCP_REGION="us-central1"
export API_ENV_FILE="services/api/.env.production"
export WORKER_ENV_FILE="services/api/.env.production"
export WEB_BUCKET="aura360-web-prod"

./deploy_all_gcloud.sh
```

**Opciones interactivas**:
1. Todos (API + Worker + Web)
2. Solo Backend (API + Worker)
3. Solo API
4. Solo Worker
5. Solo Web

---

### `deploy_api_gcloud.sh`

Script principal para ejecutar las pruebas de integración del ecosistema completo.

**Uso**:

```bash
# Ejecutar todas las pruebas
./scripts/run_integration_tests.sh

# Solo servicio vectorial
./scripts/run_integration_tests.sh --only-vectorial

# Solo servicio de agentes
./scripts/run_integration_tests.sh --only-agents

# Solo backend
./scripts/run_integration_tests.sh --only-backend

# Solo end-to-end
./scripts/run_integration_tests.sh --only-e2e

# Con cobertura
./scripts/run_integration_tests.sh --coverage

# Verbose
./scripts/run_integration_tests.sh --verbose

# Omitir verificación de servicios
./scripts/run_integration_tests.sh --skip-setup

# Ver ayuda
./scripts/run_integration_tests.sh --help
```

**Prerequisitos**:

- Todos los servicios deben estar corriendo:
  - Servicio Vectorial (puerto 8001)
  - Servicio de Agentes (puerto 8080)
  - Backend Django (puerto 8000)
- Variables de entorno configuradas correctamente
- Python 3.11+ y pytest instalados

**Output**:

Los reportes de pruebas se guardan en `test-reports/TIMESTAMP/`:

```
test-reports/
└── 20251027_143022/
    ├── Servicio_Vectorial.xml
    ├── Servicio_de_Agentes.xml
    ├── Backend_Django.xml
    └── End-to-End.xml
```

---

### `deploy_api_gcloud.sh`

Automatiza el build y deployment del backend Django en Cloud Run.

**Uso mínimo**

```bash
export GCP_PROJECT=aura360-prod
export API_ENV_FILE=deploy/api.env
./scripts/deploy_api_gcloud.sh
```

Variables opcionales: `GCP_REGION`, `API_SERVICE_NAME`, `API_MIN_INSTANCES`, `API_SERVICE_ACCOUNT`,
etc. El archivo `API_ENV_FILE` debe contener líneas `KEY=VALUE` sin comillas para propagarlas via
`--set-env-vars`.

---

### `deploy_worker_gcloud.sh`

Despliega un servicio adicional de Cloud Run que ejecuta el worker de Celery utilizando el script
`services/api/scripts/start_celery_worker.sh`. Reutiliza la misma imagen del backend y mantiene una
instancia mínima procesando la cola `holistic_snapshots`.

**Uso**

```bash
export GCP_PROJECT=aura360-prod
export WORKER_ENV_FILE=deploy/api.env
./scripts/deploy_worker_gcloud.sh
```

Puedes cambiar cola/concurrencia con `CELERY_QUEUE` y `CELERY_CONCURRENCY`.

---

### `deploy_web_gcloud.sh`

Compila la app Angular (`apps/web`), crea/actualiza un bucket de Cloud Storage y sincroniza los
artefactos estáticos. Ideal para hosting + Cloud CDN.

**Uso**

```bash
export GCP_PROJECT=aura360-prod
export WEB_BUCKET=aura360-web-static
./scripts/deploy_web_gcloud.sh
```

Variables: `WEB_DIR`, `WEB_BUILD_COMMAND`, `WEB_CACHE_CONTROL`, etc.

---

## 🔍 Scripts de Verificación

### `verify_deployments.sh`

Script completo para verificar el estado de todos los despliegues en Google Cloud.

**Uso**:
```bash
./scripts/verify_deployments.sh
```

**Verifica**:
- ✅ Autenticación de GCP
- 🚀 Estado de servicios Cloud Run (API, Celery, Agents, VectorDB)
- 🌐 Estado del frontend en Cloud Storage
- 📦 Imágenes de contenedor en GCR
- 🔧 Recursos relacionados (VPC Connectors, Secret Manager)
- 💰 Resumen de servicios activos

**Output**: Reporte detallado con colores indicando estado de cada componente.

---

### `test_deployments_e2e.sh`

Ejecuta pruebas end-to-end en los servicios desplegados.

**Uso**:
```bash
./scripts/test_deployments_e2e.sh
```

**Prueba**:
- 🔍 Health checks de todos los servicios
- 🔌 Endpoints públicos de API
- 🤖 Endpoints de Agents
- 📊 Endpoints de VectorDB
- 🌐 Accesibilidad del frontend
- 🔗 Conectividad entre servicios

**Output**: Resultados de cada prueba con status codes y respuestas.

---

## ⚙️ Scripts de Configuración

### `setup_env_production.sh`

Script interactivo para configurar archivos `.env.production` de manera guiada.

**Uso**:
```bash
./scripts/setup_env_production.sh
```

**Configura**:
1. **API Service**:
   - Django settings (SECRET_KEY auto-generado)
   - Supabase (Database + Auth)
   - Kafka/Confluent Cloud
   - Redis/Upstash
   - URLs de servicios externos

2. **Agents Service**:
   - Google Gemini API Key
   - Qdrant Cloud
   - Kafka configuration

3. **VectorDB Service**:
   - Qdrant configuration
   - Redis configuration
   - Kafka configuration

**Output**: Archivos `.env.production` listos para deployment.

---

## 🧪 Scripts de Testing

### `run_integration_tests.sh`

Script principal para ejecutar las pruebas de integración del ecosistema completo.

**Uso**:
```bash
# Ejecutar todas las pruebas
./scripts/run_integration_tests.sh

# Con cobertura
./scripts/run_integration_tests.sh --coverage

# Ver ayuda
./scripts/run_integration_tests.sh --help
```

Ver documentación original más arriba para detalles completos.

---

## 📚 Documentación Adicional

### Guías de Deployment
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Guía completa de deployment (Railway + Confluent)
- [DEPLOYMENT_GCLOUD.md](../docs/DEPLOYMENT_GCLOUD.md) - Documentación técnica de Google Cloud
- [DEPLOYMENT_CHECKLIST.md](../DEPLOYMENT_CHECKLIST.md) - Checklist paso a paso
- [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md) - Estado actual y plan de deployment

### Guías de Testing
- [INTEGRATION_TESTING.md](../docs/INTEGRATION_TESTING.md) - Guía completa de pruebas de integración
- [TESTING.md](../services/api/TESTING.md) - Testing del backend Django

### Documentación de Servicios
- [API Backend](../services/api/README.md) - Django REST API
- [Agents Service](../services/agents/README.md) - Google ADK Agents
- [VectorDB Service](../services/vectordb/README.md) - FastAPI + Qdrant

---

## 🎯 Flujo de Trabajo Recomendado

### Primera Vez (Deployment Inicial)

1. **Configurar variables de entorno**:
   ```bash
   ./scripts/setup_env_production.sh
   ```

2. **Validar configuración**:
   ```bash
   ./services/api/scripts/validate_production_env.sh services/api/.env.production
   ```

3. **Desplegar servicios**:
   ```bash
   export GCP_PROJECT="aura-360-471711"
   export GCP_REGION="us-central1"
   export API_ENV_FILE="services/api/.env.production"
   export WORKER_ENV_FILE="services/api/.env.production"
   
   ./deploy_all_gcloud.sh
   ```

4. **Verificar deployment**:
   ```bash
   ./scripts/verify_deployments.sh
   ```

5. **Ejecutar pruebas E2E**:
   ```bash
   ./scripts/test_deployments_e2e.sh
   ```

6. **Actualizar URLs cruzadas**:
   - Editar `services/api/.env.production` con las URLs reales
   - Re-desplegar: `./scripts/deploy_api_gcloud.sh`

### Updates Subsecuentes

1. **Verificar estado actual**:
   ```bash
   ./scripts/verify_deployments.sh
   ```

2. **Desplegar cambios** (servicios específicos):
   ```bash
   ./scripts/deploy_api_gcloud.sh        # Solo API
   ./scripts/deploy_worker_gcloud.sh     # Solo Worker
   ./scripts/deploy_web_gcloud.sh        # Solo Frontend
   ```

3. **Verificar deployment**:
   ```bash
   ./scripts/test_deployments_e2e.sh
   ```

---

## 🔧 Desarrollo

### Agregar Nuevos Scripts

1. Crear el script en este directorio
2. Darle permisos de ejecución: `chmod +x scripts/nuevo_script.sh`
3. Documentarlo en este README
4. Seguir las convenciones del proyecto

### Convenciones

- Usar `#!/bin/bash` como shebang
- Incluir comentarios descriptivos
- Usar `set -e` para salir en errores
- Validar prerequisitos antes de ejecutar
- Proporcionar mensajes de error claros
- Usar colores para output (ver `run_integration_tests.sh` como ejemplo)

---

## 📊 Estado de Deployment

Para verificar el estado actual de los servicios desplegados, consulta:
- [DEPLOYMENT_STATUS.md](../DEPLOYMENT_STATUS.md) - Estado actualizado de todos los servicios

Para ver logs en tiempo real:
```bash
# API logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-api" \
    --project aura-360-471711

# Worker logs
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-celery" \
    --project aura-360-471711
```

---

## 🔧 Comandos Útiles de GCloud

```bash
# Listar servicios desplegados
gcloud run services list --project aura-360-471711 --region us-central1

# Describir un servicio
gcloud run services describe aura360-api --project aura-360-471711 --region us-central1

# Ver revisiones
gcloud run revisions list --service aura360-api --project aura-360-471711 --region us-central1

# Rollback a revisión anterior
gcloud run services update-traffic aura360-api \
    --to-revisions REVISION_NAME=100 \
    --project aura-360-471711 \
    --region us-central1

# Ver logs recientes
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=aura360-api" \
    --project aura-360-471711 \
    --limit 50 \
    --format "table(timestamp,textPayload)"
```

---

**Última actualización**: Noviembre 13, 2025
