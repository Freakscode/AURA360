# 🔐 Guía de Recopilación de Credenciales - AURA360

**Fecha:** 13 de noviembre, 2025  
**Objetivo:** Recopilar todas las credenciales necesarias para deployment a GCP

---

## 📋 Checklist de Credenciales

### ✅ Servicios a Configurar

- [ ] **Supabase** - Database + Auth
- [ ] **Confluent Cloud** - Kafka (Event Streaming)
- [ ] **Upstash** - Redis (Celery + Cache)
- [ ] **Qdrant Cloud** - Vector Database
- [ ] **Google Gemini** - AI/LLM API

---

## 1️⃣ Supabase (Database + Authentication)

### 🔗 Acceder a la Consola
1. Ve a: https://supabase.com/dashboard
2. Selecciona tu proyecto AURA360

### 📊 Recopilar Credenciales de Database

**Navega a:** `Settings` → `Database`

#### Connection Pooling (Recomendado para producción)
Busca la sección "Connection Pooling" y anota:

```bash
Host: __________________________________.pooler.supabase.com
Port: 6543 (pooling) o 5432 (directo)
Database: postgres
User: postgres.____________________
Password: [RESET PASSWORD si es necesario]
```

**💡 Tip:** Si no tienes la password, haz clic en "Reset database password"

#### Connection String Completa
```
postgresql://postgres.XXXXX:PASSWORD@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### 🔑 Recopilar Credenciales de API

**Navega a:** `Settings` → `API`

```bash
Project URL: https://________________________.supabase.co
Project Ref: ________________________
anon public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key (secret): eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 🔐 Recopilar JWT Secret

**Navega a:** `Settings` → `API` → Scroll down

```bash
JWT Secret: ________________________________
```

### 📝 URLs a Configurar

```bash
SUPABASE_URL=https://XXXXX.supabase.co
SUPABASE_JWKS_URL=https://XXXXX.supabase.co/auth/v1/.well-known/jwks.json
```

#### ✅ Verificar JWKS URL
Abre en el navegador: `https://TU_PROJECT_REF.supabase.co/auth/v1/.well-known/jwks.json`
Debe devolver un JSON con las keys.

---

## 2️⃣ Confluent Cloud (Apache Kafka)

### 🔗 Acceder a la Consola
1. Ve a: https://confluent.cloud
2. Selecciona tu Environment y Cluster

### 📡 Obtener Bootstrap Servers

**Navega a:** `Cluster` → `Cluster Settings` → `Cluster Overview`

```bash
Bootstrap server: pkc-______.us-east-1.aws.confluent.cloud:9092
```

**💡 Formato esperado:** `pkc-XXXXX.REGION.aws.confluent.cloud:9092`

### 🔑 Crear/Obtener API Keys

**Navega a:** `Cluster` → `API Keys` → `Add Key`

1. Selecciona: **Cluster-specific**
2. Scope: **All topics** (o específicos si prefieres)
3. **⚠️ IMPORTANTE:** Copia inmediatamente el API Secret, no podrás verlo después

```bash
API Key: ________________________________
API Secret: ________________________________
```

### 📊 Verificar Topics Creados

**Navega a:** `Cluster` → `Topics`

Asegúrate de tener estos topics:
- [ ] `aura360.user.events`
- [ ] `aura360.context.aggregated`
- [ ] `aura360.context.vectorized`
- [ ] `aura360.guardian.requests`
- [ ] `aura360.guardian.responses`
- [ ] `aura360.vectordb.ingest`

**Si no existen, créalos:**
- Partitions: 3
- Retention: 7 days (604800000 ms)
- Cleanup policy: delete

---

## 3️⃣ Upstash (Redis - Celery Broker)

### 🔗 Acceder a la Consola
1. Ve a: https://console.upstash.com
2. Selecciona o crea tu database Redis

### 📝 Obtener Credenciales

**En el Dashboard de tu database:**

```bash
Endpoint: __________________________.upstash.io
Port: 6379
Redis URL: rediss://default:________________@___________.upstash.io:6379
```

**💡 Importante:** 
- Debe usar `rediss://` (con doble 's' para TLS)
- Incluir la password en la URL

### 🔧 Configuración para Celery

```bash
# Broker (para tareas)
CELERY_BROKER_URL=rediss://default:PASSWORD@HOST.upstash.io:6379/0

# Result Backend (para resultados)
CELERY_RESULT_BACKEND=rediss://default:PASSWORD@HOST.upstash.io:6379/1
```

**Nota:** Usamos DB 0 para broker y DB 1 para result backend.

### 💰 Plan Recomendado
- **Free tier:** 10K comandos/día (puede ser insuficiente para Celery)
- **Recomendado:** Paid tier $10/mes (100K comandos/día)

---

## 4️⃣ Qdrant Cloud (Vector Database)

### 🔗 Acceder a la Consola
1. Ve a: https://cloud.qdrant.io
2. Selecciona tu cluster o crea uno nuevo

### 📊 Crear/Seleccionar Cluster

Si necesitas crear uno:
- Name: `aura360-prod`
- Region: `us-east-1` (mismo que otros servicios)
- Plan: **Free** (1GB) para empezar

### 🔑 Obtener Credenciales

**En el Dashboard del cluster:**

```bash
Cluster URL: https://________-____.us-east-1.aws.cloud.qdrant.io:6333
API Key: qc_________________________________
```

### 📦 Collections

Las collections se crearán automáticamente:
- `holistic_memory` - Para agentes holísticos
- `user_context` - Para contexto de usuarios

**No necesitas crearlas manualmente.**

### ✅ Verificar Conectividad

Puedes probar la conexión:
```bash
curl -X GET "https://YOUR_CLUSTER_URL:6333/collections" \
     -H "api-key: YOUR_API_KEY"
```

---

## 5️⃣ Google Gemini (AI API)

### 🔗 Obtener API Key

1. Ve a: https://aistudio.google.com/app/apikey
2. O: https://makersuite.google.com/app/apikey
3. Crea un nuevo API Key o usa uno existente

```bash
Google API Key: AIzaSy________________________________
```

### ⚙️ Modelos Utilizados

AURA360 usa:
- `gemini-pro` - Para generación de texto
- `models/text-embedding-004` - Para embeddings

**Verifica que tu API Key tenga acceso a estos modelos.**

### 💰 Costos

- Gemini tiene un free tier generoso
- Revisa límites en: https://ai.google.dev/pricing

---

## 📝 Formulario de Recopilación

### Supabase
```yaml
DB_HOST: __________________________________.pooler.supabase.com
DB_PORT: 6543
DB_NAME: postgres
DB_USER: postgres.____________________
DB_PASSWORD: ________________________________
SUPABASE_URL: https://________________________.supabase.co
SUPABASE_SERVICE_ROLE_KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET: ________________________________
```

### Kafka (Confluent Cloud)
```yaml
KAFKA_BOOTSTRAP_SERVERS: pkc-______.us-east-1.aws.confluent.cloud:9092
KAFKA_API_KEY: ________________________________
KAFKA_API_SECRET: ________________________________
```

### Redis (Upstash)
```yaml
REDIS_URL: rediss://default:________________@___________.upstash.io:6379
```

### Qdrant Cloud
```yaml
QDRANT_URL: https://________-____.us-east-1.aws.cloud.qdrant.io:6333
QDRANT_API_KEY: qc_________________________________
```

### Google Gemini
```yaml
GOOGLE_API_KEY: AIzaSy________________________________
```

---

## 🚀 Siguiente Paso

Una vez tengas todas las credenciales:

### Opción 1: Usar Script Interactivo (Recomendado)
```bash
./scripts/setup_env_production.sh
```

### Opción 2: Crear Manualmente

Crea `services/api/.env.production` con:

```bash
# Django Core
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DEBUG=False
ALLOWED_HOSTS=*.run.app

# Database (Supabase)
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
DB_USER=[TU_DB_USER]
DB_PASSWORD=[TU_DB_PASSWORD]
DB_HOST=[TU_DB_HOST]
DB_PORT=6543
CONN_MAX_AGE=600

# Supabase API
SUPABASE_URL=[TU_SUPABASE_URL]
SUPABASE_API_URL=[TU_SUPABASE_URL]
SUPABASE_SERVICE_ROLE_KEY=[TU_SERVICE_ROLE_KEY]
SUPABASE_JWKS_URL=[TU_SUPABASE_URL]/auth/v1/.well-known/jwks.json
SUPABASE_JWT_SECRET=[TU_JWT_SECRET]
SUPABASE_ADMIN_TIMEOUT=10

# Kafka
KAFKA_BOOTSTRAP_SERVERS=[TU_KAFKA_BOOTSTRAP]
KAFKA_API_KEY=[TU_KAFKA_KEY]
KAFKA_API_SECRET=[TU_KAFKA_SECRET]

# Redis
CELERY_BROKER_URL=[TU_REDIS_URL]/0
CELERY_RESULT_BACKEND=[TU_REDIS_URL]/1
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=540
CELERY_TASK_DEFAULT_QUEUE=api_default

# External Services (actualizar después del deploy)
VECTOR_DB_BASE_URL=https://vectordb-service-url
HOLISTIC_AGENT_SERVICE_URL=https://agents-service-url/api/holistic/v1/run
HOLISTIC_AGENT_REQUEST_TIMEOUT=120

# CORS
CORS_ALLOWED_ORIGINS=https://storage.googleapis.com
```

---

## ✅ Validación de Credenciales

Antes de desplegar, valida que:

### Supabase
```bash
# Probar conexión a base de datos
psql "postgresql://USER:PASSWORD@HOST:6543/postgres" -c "SELECT version();"

# Probar API
curl https://YOUR_PROJECT.supabase.co/rest/v1/ \
  -H "apikey: YOUR_SERVICE_ROLE_KEY"
```

### Kafka
```bash
# Crear archivo de configuración temporal
cat > /tmp/kafka.properties <<EOF
bootstrap.servers=YOUR_BOOTSTRAP_SERVERS
security.protocol=SASL_SSL
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username='YOUR_API_KEY' password='YOUR_API_SECRET';
sasl.mechanism=PLAIN
EOF

# Listar topics (requiere kafka CLI)
kafka-topics --bootstrap-server YOUR_BOOTSTRAP_SERVERS \
  --command-config /tmp/kafka.properties --list
```

### Redis
```bash
# Probar conexión
redis-cli -u "rediss://default:PASSWORD@HOST:6379" PING
```

### Qdrant
```bash
# Probar API
curl "https://YOUR_CLUSTER:6333/collections" \
  -H "api-key: YOUR_API_KEY"
```

### Google Gemini
```bash
# Probar API
curl "https://generativelanguage.googleapis.com/v1/models?key=YOUR_API_KEY"
```

---

## 🔐 Seguridad

### ⚠️ Importante

- **NUNCA** commitees credenciales a Git
- Guarda una copia segura de las credenciales (1Password, LastPass, etc.)
- Rota las credenciales cada 90 días
- Usa diferentes credenciales para dev/staging/prod
- Considera usar Google Secret Manager para producción

### 📝 Backup de Credenciales

Guarda este archivo localmente (NO en Git):
```
~/Documents/AURA360_Production_Credentials.txt
```

---

## 📞 Ayuda

Si tienes problemas obteniendo alguna credencial:

1. **Supabase:** https://supabase.com/docs
2. **Confluent Cloud:** https://docs.confluent.io/cloud/current/get-started/index.html
3. **Upstash:** https://docs.upstash.com/
4. **Qdrant:** https://qdrant.tech/documentation/
5. **Google Gemini:** https://ai.google.dev/docs

---

**Última actualización:** 13 de noviembre, 2025  
**Tiempo estimado:** 30-45 minutos  
**Dificultad:** Intermedia

