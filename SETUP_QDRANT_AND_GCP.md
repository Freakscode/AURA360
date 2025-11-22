# 🚀 Setup Completo: Qdrant Cloud + GCP Auth

Este documento consolida los pasos para configurar Qdrant Cloud y la autenticación moderna de GCP.

---

## 📋 Pre-requisitos

- ✅ API Key de Qdrant Cloud (ya la tienes)
- ✅ Cuenta de Google Cloud
- ✅ `gcloud` CLI instalado
- ✅ Proyecto GCP: `aura-360-471711`

---

## Parte 1: Obtener URL de Qdrant Cloud

### Paso 1.1: Acceder a la Consola

1. Ir a: **https://cloud.qdrant.io**
2. **Login** con tu cuenta
3. Buscar tu **cluster** en el dashboard

### Paso 1.2: Copiar la URL del Cluster

En la página del cluster, encontrarás:

```
Cluster URL: https://XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX.us-central1-0.gcp.cloud.qdrant.io:6333
```

**Formato típico**:
```
https://<cluster-id>.<region>.gcp.cloud.qdrant.io:6333
```

**Ejemplos de regiones**:
- `us-central1-0` (Iowa)
- `us-east1-0` (South Carolina)
- `europe-west1-0` (Belgium)

### Paso 1.3: Test Rápido de Conexión

```bash
# Reemplaza con tu URL y API Key
curl -H "api-key: TU_API_KEY" \
  https://tu-cluster.us-central1-0.gcp.cloud.qdrant.io:6333/collections

# Debería retornar JSON (lista de colecciones, posiblemente vacía)
```

---

## Parte 2: Configurar Autenticación GCP Moderna

### ⚠️ Problema Actual

Estás usando **autenticación con archivos** (deprecada):
```yaml
# DEPRECADO ❌
GOOGLE_APPLICATION_CREDENTIALS=/gcloud/application_default_credentials.json
volumes:
  - ${HOME}/.config/gcloud:/gcloud:ro
```

### ✅ Solución Moderna: Application Default Credentials (ADC)

Ya he actualizado el código para usar ADC. Solo necesitas configurarlo.

### Paso 2.1: Ejecutar Script de Setup

```bash
# Desde la raíz del proyecto
./scripts/setup_gcp_auth.sh
```

Este script:
1. ✅ Verifica `gcloud` CLI
2. ✅ Autentica tu usuario (`gcloud auth login`)
3. ✅ Configura ADC (`gcloud auth application-default login`)
4. ✅ Configura proyecto por defecto (`aura-360-471711`)
5. ✅ Verifica permisos de Storage

### Paso 2.2: Configuración Manual (Alternativa)

Si prefieres hacerlo manualmente:

```bash
# 1. Login con tu cuenta de Google
gcloud auth login

# 2. Configurar Application Default Credentials
gcloud auth application-default login

# 3. Configurar proyecto
gcloud config set project aura-360-471711

# 4. Verificar
gcloud auth application-default print-access-token
```

### Paso 2.3: Verificar ADC

```bash
# El archivo debe existir
ls -la ~/.config/gcloud/application_default_credentials.json

# Debería mostrar: -rw------- ... application_default_credentials.json
```

---

## Parte 3: Configurar Variables de Entorno

### Paso 3.1: VectorDB Service

Editar `services/vectordb/.env`:

```bash
# ==============================================================================
# QDRANT CLOUD CONFIGURATION
# ==============================================================================

# URL del cluster (copiar de Qdrant Console)
QDRANT_URL=https://tu-cluster-id.us-central1-0.gcp.cloud.qdrant.io:6333

# API Key de Qdrant Cloud
QDRANT_API_KEY=tu-api-key-aqui

# NO usar gRPC con Qdrant Cloud
QDRANT_GRPC=
PREFER_GRPC=false

# Collection Configuration
VECTOR_COLLECTION_NAME=holistic_memory
VECTOR_DIMENSION=384
VECTOR_DISTANCE=cosine

# ==============================================================================
# GCP CONFIGURATION (Autenticación moderna - ADC)
# ==============================================================================

# Proyecto GCP
GCS_PROJECT=aura-360-471711
```

### Paso 3.2: Agents Service

Editar `services/agents/.env`:

```bash
# ==============================================================================
# QDRANT CLOUD CONFIGURATION
# ==============================================================================

# URL del cluster (la misma que vectordb)
AGENT_SERVICE_QDRANT_URL=https://tu-cluster-id.us-central1-0.gcp.cloud.qdrant.io:6333

# API Key de Qdrant Cloud
AGENT_SERVICE_QDRANT_API_KEY=tu-api-key-aqui

# Collection name
AGENT_SERVICE_VECTOR_COLLECTION=holistic_memory

# SSL verification (Qdrant Cloud usa HTTPS)
AGENT_SERVICE_VECTOR_VERIFY_SSL=true
```

---

## Parte 4: Crear Colecciones en Qdrant Cloud

### Paso 4.1: Ejecutar Script de Inicialización

```bash
cd services/vectordb

# Configurar variables de entorno primero
export QDRANT_URL="https://tu-cluster.us-central1-0.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="tu-api-key"

# Crear colecciones
python scripts/init_qdrant_collections.py
```

**Output esperado**:
```
======================================================================
  Inicialización de Colecciones en Qdrant Cloud - AURA360
======================================================================

🔗 Conectando a Qdrant: https://...
✅ Conexión exitosa a Qdrant

📦 Creando colección 'holistic_memory'...
   Almacena embeddings de contexto de usuario y documentos holísticos
   Dimensión: 384, Distancia: Cosine
✅ Colección 'holistic_memory' creada exitosamente

📦 Creando colección 'user_context'...
   Almacena contexto agregado de usuarios
   Dimensión: 384, Distancia: Cosine
✅ Colección 'user_context' creada exitosamente

📦 Creando colección 'holistic_agents'...
   Almacena embeddings para el servicio de agents (RAG)
   Dimensión: 768, Distancia: Cosine
✅ Colección 'holistic_agents' creada exitosamente

======================================================================
✅ Inicialización completada: 3/3 colecciones
======================================================================
```

---

## Parte 5: Verificar Integración Completa

### Paso 5.1: Ejecutar Script de Verificación

```bash
# Desde la raíz del proyecto
./scripts/verify_qdrant_integration.sh
```

Este script verifica:
1. ✅ VectorDB Service puede conectarse a Qdrant Cloud
2. ✅ Agents Service puede conectarse a Qdrant Cloud
3. ✅ Todas las colecciones requeridas existen

### Paso 5.2: Test Manual de Conexión

#### Desde VectorDB Service:

```bash
cd services/vectordb
source .env

python -c "
from qdrant_client import QdrantClient
import os

client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

collections = client.get_collections()
print('✅ Conexión exitosa')
print(f'📦 Colecciones: {[c.name for c in collections.collections]}')
"
```

#### Desde Agents Service:

```bash
cd services/agents
source .env

python -c "
from qdrant_client import QdrantClient
import os

client = QdrantClient(
    url=os.getenv('AGENT_SERVICE_QDRANT_URL'),
    api_key=os.getenv('AGENT_SERVICE_QDRANT_API_KEY')
)

collections = client.get_collections()
print('✅ Agents conectado a Qdrant Cloud')
print(f'📦 Colecciones: {[c.name for c in collections.collections]}')
"
```

---

## Parte 6: Levantar Servicios

### Paso 6.1: Docker Compose (Desarrollo Local)

```bash
cd services/vectordb

# Levantar servicios
docker compose up -d

# Verificar estado
docker compose ps

# Ver logs
docker logs vectordb-vectordb-consumer-1 --tail 50
```

**Estado esperado**:
```
NAME                           STATUS
vectordb-qdrant-1              Up 4 days
vectordb-redis-1               Up 4 days
vectordb-grobid-1              Up 4 days
vectordb-vectordb-consumer-1   Up 2 minutes
```

### Paso 6.2: Verificar Consumer de Kafka

```bash
docker logs vectordb-vectordb-consumer-1 --tail 20
```

**Output esperado**:
```
2025-11-20 12:57:42 | INFO | 🚀 Starting Vectordb Kafka Consumer
2025-11-20 12:57:42 | INFO |    Embedding Model: sentence-transformers/all-MiniLM-L6-v2
2025-11-20 12:57:42 | INFO |    Qdrant URL: http://qdrant:6333
2025-11-20 12:57:42 | INFO |    Collection: holistic_memory
2025-11-20 12:57:42 | INFO | 📥 Registered handlers:
2025-11-20 12:57:42 | INFO |    - user.mood.created → aggregate context
2025-11-20 12:57:42 | INFO |    - user.activity.created → aggregate context
2025-11-20 12:57:42 | INFO |    - context.aggregated → vectorize and ingest
2025-11-20 12:57:42 | INFO | 🎧 Consumer ready, waiting for events...
```

---

## ✅ Checklist Final

### Configuración Qdrant Cloud
- [ ] Obtener URL del cluster desde https://cloud.qdrant.io
- [ ] Copiar API Key
- [ ] Actualizar `QDRANT_URL` en `.env` de vectordb
- [ ] Actualizar `QDRANT_API_KEY` en `.env` de vectordb
- [ ] Actualizar `AGENT_SERVICE_QDRANT_URL` en `.env` de agents
- [ ] Actualizar `AGENT_SERVICE_QDRANT_API_KEY` en `.env` de agents

### Autenticación GCP
- [ ] Ejecutar `./scripts/setup_gcp_auth.sh`
- [ ] Verificar archivo ADC existe: `~/.config/gcloud/application_default_credentials.json`
- [ ] Configurar proyecto: `gcloud config set project aura-360-471711`

### Colecciones en Qdrant
- [ ] Ejecutar `python scripts/init_qdrant_collections.py`
- [ ] Verificar 3 colecciones creadas:
  - `holistic_memory` (384 dim, Cosine)
  - `user_context` (384 dim, Cosine)
  - `holistic_agents` (768 dim, Cosine)

### Verificación
- [ ] Ejecutar `./scripts/verify_qdrant_integration.sh`
- [ ] VectorDB Service conecta a Qdrant Cloud ✅
- [ ] Agents Service conecta a Qdrant Cloud ✅
- [ ] Consumer de Kafka está corriendo ✅

### Servicios
- [ ] `docker compose up -d` en `services/vectordb`
- [ ] Todos los servicios corriendo
- [ ] Consumer de Kafka sin errores de importación

---

## 🆘 Troubleshooting

### No encuentro la URL de Qdrant Cloud

1. Ir a https://cloud.qdrant.io
2. Verificar que estés en la cuenta correcta
3. Si no ves ningún cluster, crear uno nuevo:
   - Click "Create Cluster"
   - Provider: Google Cloud Platform
   - Region: us-central1 (Iowa)
   - Tier: Free (desarrollo) o Starter (producción)

### Error: "Permission denied" en GCS

```bash
# Verificar permisos
gcloud projects get-iam-policy aura-360-471711 \
  --flatten="bindings[].members" \
  --filter="bindings.members:user:$(gcloud config get-value account)"

# Si no tienes permisos, contactar al admin del proyecto
```

### Error: "Connection refused" a Qdrant

- Verificar que el cluster esté "Running" en Qdrant Console
- Verificar que la URL incluya el puerto `:6333`
- Verificar que la API key sea correcta
- Test con curl (ver Paso 1.3)

### Consumer de Kafka en crash loop

Ya lo arreglamos. Si vuelve a pasar:
```bash
# Reconstruir imagen
cd services/vectordb
docker compose build vectordb-consumer
docker compose up -d vectordb-consumer
```

---

## 📚 Documentación Adicional

- **Qdrant Cloud Setup**: `infra/gcp/QDRANT_CLOUD_SETUP.md`
- **GCP Auth Migration**: `infra/gcp/GCP_AUTH_MIGRATION.md`
- **Integration Guide**: `docs/QDRANT_INTEGRATION_GUIDE.md`
- **Get Qdrant URL**: `GET_QDRANT_URL.md`

---

## 🎉 ¡Listo!

Una vez completados todos los pasos, tendrás:

✅ Qdrant Cloud configurado y accesible
✅ Autenticación GCP moderna (ADC)
✅ Colecciones creadas en Qdrant
✅ Todos los servicios conectados
✅ Consumer de Kafka funcionando

**Próximos pasos**:
1. Poblar la base de conocimiento con documentos
2. Probar la integración end-to-end
3. Desplegar en GKE con Workload Identity
