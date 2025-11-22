# AURA360 - Guía de Deployment a Producción
**Railway + Confluent Cloud + Qdrant Cloud + Upstash Redis**

Generado: 2025-01-07 (Actualizado con Arquitectura Event-Driven)

---

## 📋 Pre-requisitos

### Cuentas Necesarias
- ✅ Railway (https://railway.app) - **Gratis para empezar**
- ✅ **Confluent Cloud (https://confluent.cloud) - 1 AÑO GRATIS** 🎉
- ✅ Qdrant Cloud (https://cloud.qdrant.io) - **Free tier: 1GB**
- ✅ Upstash Redis (https://upstash.com) - **Free tier: 10K cmd/día** (recomendado upgrade a $10/mes)
- ✅ Supabase (ya configurado)
- ✅ Google Cloud (API Key para Gemini)

### Herramientas
```bash
# Railway CLI
brew install railway

# Docker (para builds locales de testing)
brew install --cask docker
```

---

## 🔑 Variables de Entorno - Configuración Completa

### 1. Django API Service (`services/api`)

**SECRETS** (Railway Secret Variables):
```bash
# Django
SECRET_KEY=mb&$nx0b%k(+735@ihq744d*vp(a!-eo-#2psju-gd%$gqjgdn
DEBUG=False

# Supabase
SUPABASE_SERVICE_ROLE_KEY=<tu-service-role-key>
SUPABASE_JWT_SECRET=<opcional-si-usas-jwks>
SUPABASE_JWKS_URL=https://<tu-proyecto>.supabase.co/auth/v1/.well-known/jwks.json

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://<user>:<password>@<host>:6543/postgres
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=postgres.nxxxx
DB_PASSWORD=<tu-password>
DB_HOST=aws-0-us-east-1.pooler.supabase.com
DB_PORT=6543
```

**CONFIG** (Railway Variables):
```bash
# Django Settings
ALLOWED_HOSTS=api-production.up.railway.app,api.aura360.app
CORS_ALLOWED_ORIGINS=https://web-production.up.railway.app,https://app.aura360.app

# Supabase
SUPABASE_URL=https://<tu-proyecto>.supabase.co

# External Services
VECTOR_DB_BASE_URL=https://vectordb-api-production.up.railway.app
HOLISTIC_AGENT_SERVICE_URL=https://agents-production.up.railway.app/api/holistic/v1/run

# Celery (opcional para Django)
BROKER_URL=<redis-url>/0
RESULT_BACKEND=<redis-url>/1
```

---

### 2. Agents Service (`services/agents`)

**SECRETS**:
```bash
# Google Gemini API
GOOGLE_API_KEY=<tu-google-api-key>

# Qdrant Cloud
AGENT_SERVICE_QDRANT_API_KEY=<tu-qdrant-api-key>
```

**CONFIG**:
```bash
# Qdrant
AGENT_SERVICE_QDRANT_URL=https://<tu-cluster>.us-east-1.aws.cloud.qdrant.io:6333
AGENT_SERVICE_VECTOR_COLLECTION=holistic_memory
AGENT_SERVICE_VECTOR_VERIFY_SSL=true
AGENT_SERVICE_VECTOR_TOP_K=5
AGENT_SERVICE_VECTOR_RETRIES=2

# Embedding Configuration
AGENT_DEFAULT_EMBEDDING_MODEL=models/text-embedding-004
AGENT_SERVICE_EMBEDDING_BACKEND=gemini
AGENT_SERVICE_EMBEDDING_NORMALIZE=true

# Service Configuration
AGENT_SERVICE_TIMEOUT=30
AGENT_SERVICE_MODEL_VERSION=1.0.0
AGENT_SERVICE_RECOMMENDATION_HORIZON_DAYS=21
```

---

### 3. Vectordb API Service (`services/vectordb-api`)

**SECRETS**:
```bash
# Qdrant Cloud
QDRANT_API_KEY=<tu-qdrant-api-key>

# Upstash Redis
REDIS_URL=rediss://default:<password>@us-east-1.upstash.io:6379
```

**CONFIG**:
```bash
# Qdrant
QDRANT_URL=https://<tu-cluster>.us-east-1.aws.cloud.qdrant.io:6333
QDRANT_GRPC=<tu-cluster>.us-east-1.aws.cloud.qdrant.io:6334
PREFER_GRPC=false

# Redis (Celery Broker & Cache)
BROKER_URL=${REDIS_URL}/0
RESULT_BACKEND=${REDIS_URL}/1
CACHE_EMBEDDINGS=true
CACHE_EMBEDDING_TTL=604800

# Vector Configuration
VECTOR_COLLECTION_NAME=holistic_memory
VECTOR_DISTANCE=cosine
DEFAULT_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_VERSION=2025.10.27
EMBEDDING_DIM=384

# Topic Classification
AUTO_TOPICS=true
TOPIC_TOP_K=3
TOPIC_THRESHOLD=0.34

# GROBID - ❌ NO USAR en Railway (no disponible)
# GROBID_URL=  # Dejar vacío, usará PyMuPDF fallback
```

---

### 4. Vectordb Worker Service (`services/vectordb-worker`)

**SECRETS & CONFIG**:
- ✅ **Idénticas a vectordb-api** (comparten configuración)
- Solo cambia el comando de inicio (Celery worker en lugar de uvicorn)

**ADICIONALES**:
```bash
# Celery Worker Specific
CELERY_CONCURRENCY=2
WEB_CONCURRENCY=2
```

---

### 5. Angular Web Service (`apps/web`)

**PUBLIC VARIABLES** (se incluyen en el bundle del cliente):
```bash
# Supabase (anon key es seguro exponer)
SUPABASE_URL=https://<tu-proyecto>.supabase.co
SUPABASE_ANON_KEY=<tu-anon-key>

# Backend API
API_BASE_URL=https://api-production.up.railway.app

# Build
NODE_ENV=production
```

---

## 🚀 Proceso de Deployment

### Paso 0: Setup Confluent Cloud (20 min) - ⭐ NUEVO

**AURA360 usa arquitectura event-driven con Apache Kafka (Confluent Cloud) para comunicación entre servicios.**

#### 0.1 Crear Cuenta y Activar Beneficio

1. Ir a https://confluent.cloud
2. Crear cuenta (usar email corporativo si aplica)
3. **Activar perk de 1 año gratis** en el onboarding
4. Completar verificación de email

#### 0.2 Crear Environment y Cluster

```bash
# 1. Crear Environment
- Name: `aura360-production`
- Cloud provider: AWS
- Region: us-east-1 (mismo que Railway y Qdrant)

# 2. Crear Cluster
- Type: Basic (suficiente para 1 año gratis)
- Name: `aura360-kafka-prod`
- Availability: Single Zone
```

#### 0.3 Crear Topics

En Confluent Cloud UI → Topics → Create Topic:

```yaml
# Topic 1: User Events
Name: aura360.user.events
Partitions: 3
Retention: 7 days (604800000 ms)
Cleanup policy: delete

# Topic 2: Context Aggregated
Name: aura360.context.aggregated
Partitions: 3
Retention: 7 days

# Topic 3: Context Vectorized
Name: aura360.context.vectorized
Partitions: 3
Retention: 7 days

# Topic 4: Guardian Requests
Name: aura360.guardian.requests
Partitions: 3
Retention: 7 days

# Topic 5: Guardian Responses
Name: aura360.guardian.responses
Partitions: 3
Retention: 7 days

# Topic 6: Vectordb Ingest
Name: aura360.vectordb.ingest
Partitions: 3
Retention: 7 days
```

#### 0.4 Crear API Keys

1. En Confluent Cloud UI → API Keys → Add Key
2. Scope: Cluster-specific
3. Name: `aura360-all-services`
4. Permissions: Read + Write (todos los topics)
5. **Copiar y guardar**:
   - API Key: `ABCD1234XXXX`
   - API Secret: `xxxxxxxxxxxxxxxxxxxxxxxxxxxx`

⚠️ **IMPORTANTE**: Guarda el API Secret inmediatamente, no podrás verlo después.

#### 0.5 Obtener Bootstrap Servers URL

1. En Confluent Cloud → Cluster Settings
2. Copiar **Bootstrap server**:
   - Ejemplo: `pkc-xxxxx.us-east-1.aws.confluent.cloud:9092`

#### 0.6 Variables de Entorno para Confluent

Agregar a **TODOS** los servicios (Django API, Agents, Vectordb):

```bash
# Confluent Cloud - Event Streaming
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
KAFKA_API_KEY=ABCD1234XXXX
KAFKA_API_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxx
ENV=production

# Schema Registry (opcional)
KAFKA_SCHEMA_REGISTRY_URL=https://psrc-xxxxx.us-east-1.aws.confluent.cloud
```

---

### Paso 1: Setup Qdrant Cloud (10 min)

1. Ir a https://cloud.qdrant.io y crear cuenta
2. Crear cluster:
   - Name: `aura360-prod`
   - Region: `us-east-1` (mismo que Railway)
   - Plan: **Free** (1GB)
3. Esperar ~2 minutos a que cluster esté listo
4. Copiar:
   - **URL**: `https://xxxxx-xxxx.us-east-1.aws.cloud.qdrant.io:6333`
   - **API Key**: `qc_xxxxxxxxx`
5. **Importante**: Las collections (`holistic_memory`, `user_context`) se crearán automáticamente en primer ingest

---

### Paso 2: Setup Upstash Redis (10 min)

1. Ir a https://upstash.com y crear cuenta
2. Crear database:
   - Name: `aura360-cache`
   - Type: **Redis 7**
   - Region: `us-east-1`
   - TLS: **Enabled** (obligatorio)
3. Copiar:
   - **URL**: `rediss://default:xxxxxxx@us-east-1.upstash.io:6379`
4. **Recomendación**:
   - Free tier (10K cmd/día) puede ser insuficiente para Celery
   - Upgrade sugerido: **$10/mes** (100K cmd/día)

---

### Paso 3: Deploy a Railway (2-3 horas)

#### 3.1 Inicializar Proyecto

```bash
# Login
railway login

# Crear proyecto
cd /path/to/AURA360
railway init
# Nombre: aura360-production
# Region: us-east-1
```

#### 3.2 Deploy Vectordb Worker (primero)

```bash
cd services/vectordb

# Crear service
railway service create vectordb-worker

# Deploy
railway up --dockerfile Dockerfile.worker --service vectordb-worker

# Configurar variables (Railway Dashboard)
# → Ir a vectordb-worker service
# → Variables tab
# → Copiar todas las variables de "3. Vectordb Worker" arriba
```

#### 3.3 Deploy Vectordb API

```bash
# Mismo directorio
railway service create vectordb-api
railway up --dockerfile Dockerfile.api --service vectordb-api

# Configurar variables (idénticas al worker)
```

#### 3.4 Deploy Agents Service

```bash
cd ../agents

railway service create agents
railway up --service agents

# Configurar variables (ver sección "2. Agents Service")
```

#### 3.5 Deploy Django API

```bash
cd ../api

railway service create api
railway up --service api

# Configurar variables (ver sección "1. Django API Service")

# ⚠️ IMPORTANTE: Configurar Start Command en Railway Dashboard
# Settings → Deploy → Start Command:
# python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

#### 3.6 Deploy Angular Web

```bash
cd ../../apps/web

railway service create web
railway up --service web

# Configurar variables (ver sección "5. Angular Web Service")
```

---

### Paso 4: Configurar Networking (30 min)

Railway genera URLs automáticas para cada service:
```
api: https://api-production-xxxxx.up.railway.app
agents: https://agents-production-xxxxx.up.railway.app
vectordb-api: https://vectordb-api-production-xxxxx.up.railway.app
web: https://web-production-xxxxx.up.railway.app
```

**Actualizar variables cross-service**:

1. En **API service**, actualizar:
   ```
   VECTOR_DB_BASE_URL=<copiar URL de vectordb-api>
   HOLISTIC_AGENT_SERVICE_URL=<copiar URL de agents>/api/holistic/v1/run
   ```

2. En **API service**, actualizar ALLOWED_HOSTS y CORS:
   ```
   ALLOWED_HOSTS=<api-url>,api.aura360.app
   CORS_ALLOWED_ORIGINS=<web-url>,https://app.aura360.app
   ```

3. En **WEB service**, actualizar:
   ```
   API_BASE_URL=<copiar URL de api>
   ```

---

### Paso 5: Configurar Dominios Personalizados (opcional, 30 min)

Si tienes un dominio (ej: `aura360.app`):

```bash
# Agregar dominios en Railway Dashboard
# O vía CLI:

railway domain add api.aura360.app --service api
railway domain add agents.aura360.app --service agents
railway domain add vectordb.aura360.app --service vectordb-api
railway domain add app.aura360.app --service web

# Railway genera certificados SSL automáticamente
# Actualizar DNS records en tu proveedor:
# - api.aura360.app → CNAME → api-production-xxxxx.up.railway.app
# - agents.aura360.app → CNAME → agents-production-xxxxx.up.railway.app
# etc.
```

---

## ✅ Testing & Validación

### Health Checks

```bash
# API
curl https://<api-url>/api/v1/health
# Esperado: {"status":"ok"}

# Agents
curl https://<agents-url>/readyz
# Esperado: {"status":"ok"}

# Vectordb
curl https://<vectordb-url>/readyz
# Esperado: {"status":"ok"}

# Web
curl https://<web-url>
# Esperado: HTML response (200 OK)
```

### Integration Test

1. **Login desde Angular app**: Ir a `<web-url>`
2. **Crear mood entry**: Navegar a mood tracker
3. **Verificar en Railway logs**:
   - API: Log de POST `/api/holistic/mood-entries/`
   - Vectordb Worker: Log de job procesado
4. **Verificar en Qdrant Cloud**: Dashboard → Collections → user_context → debe tener 1+ points

### Performance Monitoring

Railway dashboard → Service → Metrics:
- **CPU**: <50% normal, picos <80%
- **RAM**: API ~512MB, Agents ~1GB, Worker ~1-2GB
- **Network**: <1GB/día en free tier

---

## 💰 Costos Estimados

### Mes 1 (MVP, <100 usuarios)
| Servicio | Plan | Costo |
|----------|------|-------|
| Railway (5 services) | Starter | $40-60/mes |
| Qdrant Cloud | Free | $0 |
| Upstash Redis | Paid ($10) | $10/mes |
| Supabase | Pro | $25/mes |
| **Total** | | **$75-95/mes** |

### Mes 3-6 (Growth, 100-1K usuarios)
| Servicio | Plan | Costo |
|----------|------|-------|
| Railway | Pro | $60-80/mes |
| Qdrant Cloud | Starter (5GB) | $25/mes |
| Upstash Redis | Pro | $10/mes |
| Supabase | Pro | $25/mes |
| **Total** | | **$120-140/mes** |

---

## 🐛 Troubleshooting

### Error: "Database connection refused"
- **Causa**: DB_PORT incorrecto
- **Solución**: Usar puerto `6543` (Supabase pooler), no `5432`

### Error: "Qdrant unauthorized"
- **Causa**: QDRANT_API_KEY no configurado
- **Solución**: Agregar `QDRANT_API_KEY` a variables de entorno

### Error: "Celery worker no procesa jobs"
- **Causa**: Redis URL incorrecto o free tier agotado
- **Solución**:
  1. Verificar REDIS_URL tiene formato `rediss://` (con TLS)
  2. Upgrade Upstash a paid tier

### Error: "CORS blocked"
- **Causa**: Dominio no en CORS_ALLOWED_ORIGINS
- **Solución**: Agregar dominio web a CORS_ALLOWED_ORIGINS en API service

### Error: "Module 'google.adk' not found"
- **Causa**: Build falló al instalar dependencias
- **Solución**: Verificar pyproject.toml tiene `google-adk>=0.0.6`

---

## 📱 Próximos Pasos: Mobile App

Una vez el backend esté en producción:

1. **Actualizar env variables en Flutter**:
   ```dart
   // apps/mobile/env/production.env
   API_BASE_URL=https://api.aura360.app
   ```

2. **Deploy a TestFlight/Play Internal**:
   - Ver guía en repositorio: `apps/mobile/README.md`
   - Timeline estimado: 1-2 semanas adicionales

3. **Beta testing con usuarios reales**

---

## 🔐 Security Checklist

- [x] Django SECRET_KEY generado (no usar el de desarrollo)
- [x] DEBUG=False en producción
- [x] ALLOWED_HOSTS configurado correctamente
- [x] CORS_ALLOWED_ORIGINS solo dominios permitidos
- [ ] Revisar Google API Key (verificar no sea el del .env.example público)
- [x] Supabase SERVICE_ROLE_KEY en secrets (no exponer)
- [x] Qdrant API Key en secrets
- [x] Upstash Redis URL en secrets
- [x] TLS/HTTPS habilitado en todos los servicios (Railway auto-configura)

---

## 📊 Monitoring & Observabilidad

### Railway Dashboard
- **Logs**: Real-time logs por servicio
- **Metrics**: CPU, RAM, Network usage
- **Deployments**: Historial de deploys, rollback fácil

### Recomendaciones Adicionales
- **Better Stack** (free tier): Alertas por email/Slack
- **Sentry** (free tier): Error tracking para Python/JavaScript
- **Uptime Robot** (free): Health check monitoring cada 5 min

---

## 🔄 Rollback Strategy

Si algo sale mal:

```bash
# Ver deploys anteriores
railway deployment list --service api

# Rollback a deploy específico
railway deployment rollback <deployment-id> --service api
```

Railway mantiene últimos 10 deploys. Rollback es instantáneo.

---

## 📞 Support

- **Railway**: https://railway.app/help
- **Qdrant**: https://qdrant.tech/documentation/
- **Upstash**: https://docs.upstash.com/

---

**Deployment completado! 🎉**

Última actualización: 2025-11-05
