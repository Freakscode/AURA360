# Guía de Integración: Frontend → Backend → Qdrant Cloud

## Visión General

Este documento describe cómo se integra AURA360 con **Qdrant Cloud** (managed vector database en GCP) para proporcionar funcionalidades de RAG (Retrieval Augmented Generation) y búsqueda semántica.

```
┌─────────────────┐
│  Angular Web    │  apps/web
│   Frontend      │
└────────┬────────┘
         │ HTTP REST API
         ↓
┌─────────────────┐
│  Django API     │  services/api:8000
│   Backend       │
└────────┬────────┘
         │ Kafka Events
         ↓
┌─────────────────┐
│  Agents Service │  services/agents:8080
│  (Google ADK)   │
└────────┬────────┘
         │ Vector Search
         │ HTTP API
         ↓
┌─────────────────┐
│  VectorDB Svc   │  services/vectordb:8001
│  (FastAPI)      │
└────────┬────────┘
         │ REST/HTTPS
         ↓
┌─────────────────┐
│  Qdrant Cloud   │  https://cluster.gcp.cloud.qdrant.io
│  (GCP Managed)  │
└─────────────────┘
```

---

## 1. Servicios y Responsabilidades

### 1.1 Frontend (Angular - `apps/web`)

**Responsabilidad**: Interfaz de usuario y llamadas HTTP al backend.

**Endpoints que consume** (del Django API):
- `POST /api/holistic/advice/` - Solicitar consejo holístico (trigger para RAG)
- `GET /api/holistic/user-context/` - Obtener contexto del usuario
- `POST /api/holistic/events/` - Enviar eventos de usuario

**Configuración**:
```typescript
// apps/web/src/environments/environment.ts
export const environment = {
  production: true,
  apiBaseUrl: 'https://api.aura360.com/api', // Django API
  supabase: { ... }
};
```

**Archivos relevantes**:
- `apps/web/src/app/core/services/*` - Servicios HTTP
- `apps/web/src/app/features/profesional/services/*` - Servicios específicos de profesionales

---

### 1.2 Django API Backend (`services/api`)

**Responsabilidad**: API REST principal, autenticación, business logic.

**Flujo de integración**:
1. Recibe requests del frontend
2. Valida autenticación (Supabase JWT)
3. Publica eventos a Kafka para procesamiento asíncrono
4. Llama directamente a Agents Service para consultas síncronas

**Conexión con Vectordb/Agents**:
```python
# services/api/holistic/context_vectorizer.py
from kafka import KafkaProducer

# Publica evento de contexto de usuario
producer.send(
    'aura360.context.aggregated',
    value=user_context_payload
)
```

**Configuración** (`services/api/.env`):
```bash
# Kafka (para eventos asíncronos)
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.confluent.cloud:9092
KAFKA_API_KEY=...
KAFKA_API_SECRET=...

# No se conecta directamente a Qdrant
# (usa Agents Service como proxy)
```

**Archivos relevantes**:
- `services/api/holistic/context_vectorizer.py` - Envía contexto a Kafka
- `services/api/holistic/views.py` - Endpoints de API
- `services/api/config/settings.py` - Configuración

---

### 1.3 Agents Service (`services/agents`)

**Responsabilidad**: Agentes de IA, RAG, generación de consejos holísticos.

**Flujo de integración**:
1. Escucha requests de Kafka (`aura360.guardian.requests`)
2. Llama a **VectorDB Service** para búsqueda semántica
3. Usa Google ADK (Gemini) para generar respuestas
4. Publica respuestas a Kafka

**Conexión con Qdrant**:
```python
# services/agents/infra/vector_store.py
from qdrant_client import QdrantClient

client = QdrantClient(
    url=os.getenv('AGENT_SERVICE_QDRANT_URL'),
    api_key=os.getenv('AGENT_SERVICE_QDRANT_API_KEY'),
)

# Búsqueda de documentos similares
results = client.search(
    collection_name="holistic_agents",
    query_vector=embedding,
    limit=5
)
```

**Configuración** (`services/agents/.env`):
```bash
# Qdrant Cloud
AGENT_SERVICE_QDRANT_URL=https://abc.us-central1-0.gcp.cloud.qdrant.io:6333
AGENT_SERVICE_QDRANT_API_KEY=your-api-key
AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents
AGENT_SERVICE_VECTOR_VERIFY_SSL=true

# Google Gemini (para embeddings y LLM)
GOOGLE_API_KEY=your-gemini-api-key
AGENT_DEFAULT_EMBEDDING_MODEL=models/text-embedding-004
```

**Archivos relevantes**:
- `services/agents/infra/vector_store.py` - Cliente de Qdrant
- `services/agents/services/vector_queries.py` - Búsqueda semántica
- `services/agents/kafka/consumer.py` - Consume eventos de Kafka

---

### 1.4 VectorDB Service (`services/vectordb`)

**Responsabilidad**: Procesamiento de PDFs, ingesta de documentos, indexación en Qdrant.

**Flujo de integración**:
1. Escucha eventos de Kafka (`aura360.vectordb.ingest`)
2. Procesa documentos (PDFs con Grobid)
3. Genera embeddings (FastEmbed o Gemini)
4. Almacena vectores en **Qdrant Cloud**

**Conexión con Qdrant**:
```python
# services/vectordb/vectosvc/core/qdrant_store.py
from qdrant_client import QdrantClient
from vectosvc.config import settings

client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
)

# Insertar vectores
client.upsert(
    collection_name=settings.collection_name,
    points=[
        {
            "id": doc_id,
            "vector": embedding,
            "payload": metadata
        }
    ]
)
```

**Configuración** (`services/vectordb/.env`):
```bash
# Qdrant Cloud
QDRANT_URL=https://abc.us-central1-0.gcp.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key
VECTOR_COLLECTION_NAME=holistic_memory
VECTOR_DIMENSION=384
PREFER_GRPC=false  # Qdrant Cloud usa REST/HTTPS

# Embeddings
DEFAULT_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_BACKEND=fastembed

# Procesamiento de PDFs
GROBID_URL=http://grobid:8070
```

**Archivos relevantes**:
- `services/vectordb/vectosvc/core/qdrant_store.py` - Cliente de Qdrant
- `services/vectordb/vectosvc/worker/tasks.py` - Tareas de Celery
- `services/vectordb/vectosvc/kafka/consumer.py` - Consumer de Kafka

---

## 2. Colecciones en Qdrant Cloud

### 2.1 `holistic_memory`
**Uso**: Almacenar embeddings de documentos y conocimiento holístico.

```json
{
  "name": "holistic_memory",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

**Contenido típico**:
- PDFs de nutrición y wellness
- Artículos médicos
- Guías de ejercicio
- Documentación de prácticas holísticas

**Servicio que escribe**: VectorDB Service
**Servicio que lee**: Agents Service

---

### 2.2 `user_context`
**Uso**: Almacenar contexto agregado de usuarios (eventos, actividades, preferencias).

```json
{
  "name": "user_context",
  "vectors": {
    "size": 384,
    "distance": "Cosine"
  }
}
```

**Contenido típico**:
- Eventos de usuario (logins, interacciones)
- Preferencias alimentarias
- Historial de actividad física
- Objetivos de salud

**Servicio que escribe**: VectorDB Service (via Kafka)
**Servicio que lee**: Agents Service

---

### 2.3 `holistic_agents`
**Uso**: Embeddings para RAG del servicio de agents (opcional, usa Gemini embeddings).

```json
{
  "name": "holistic_agents",
  "vectors": {
    "size": 768,
    "distance": "Cosine"
  }
}
```

**Contenido típico**:
- Knowledge base específico de agents
- Documentación de dominio

**Servicio que escribe**: Agents Service
**Servicio que lee**: Agents Service

---

## 3. Flujo End-to-End: Solicitar Consejo Holístico

### 3.1 Solicitud desde Frontend

```typescript
// apps/web - Usuario hace click en "Obtener consejo"
const request = {
  user_id: 'abc-123',
  query: '¿Qué ejercicios debo hacer?',
  context: {
    goals: ['perder peso', 'mejorar energía'],
    preferences: ['yoga', 'correr']
  }
};

this.http.post('/api/holistic/advice/', request).subscribe(response => {
  console.log('Consejo:', response.advice);
});
```

---

### 3.2 Django API procesa request

```python
# services/api/holistic/views.py
@api_view(['POST'])
def get_holistic_advice(request):
    # 1. Validar autenticación
    user = request.user

    # 2. Publicar evento a Kafka para procesamiento asíncrono
    producer.send('aura360.guardian.requests', {
        'user_id': user.id,
        'query': request.data['query'],
        'context': request.data['context']
    })

    # 3. Retornar respuesta inmediata o esperar (sync/async)
    return Response({'status': 'processing'})
```

---

### 3.3 Agents Service consume evento

```python
# services/agents/kafka/consumer.py
def handle_guardian_request(message):
    user_id = message['user_id']
    query = message['query']

    # 1. Generar embedding de la query
    embedding = generate_embedding(query)

    # 2. Buscar documentos similares en Qdrant
    results = qdrant_client.search(
        collection_name="holistic_memory",
        query_vector=embedding,
        limit=5
    )

    # 3. Generar respuesta con Gemini + RAG
    context_docs = [r.payload['text'] for r in results]
    advice = generate_advice_with_gemini(query, context_docs)

    # 4. Publicar respuesta a Kafka
    producer.send('aura360.guardian.responses', {
        'user_id': user_id,
        'advice': advice
    })
```

---

### 3.4 VectorDB Service (búsqueda)

```python
# services/vectordb/vectosvc/core/qdrant_store.py
def search_similar(query_vector, collection="holistic_memory", limit=5):
    results = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=limit,
        with_payload=True
    )
    return results
```

---

### 3.5 Qdrant Cloud devuelve resultados

```json
{
  "result": [
    {
      "id": "doc-123",
      "score": 0.92,
      "payload": {
        "text": "El ejercicio cardiovascular es excelente para...",
        "source": "guia-ejercicio.pdf",
        "topic": "ejercicio"
      }
    },
    {
      "id": "doc-456",
      "score": 0.87,
      "payload": {
        "text": "Para perder peso, combina ejercicio con...",
        "source": "nutricion.pdf",
        "topic": "nutrición"
      }
    }
  ]
}
```

---

## 4. Variables de Entorno Necesarias

### 4.1 Tabla Resumen

| Servicio | Variable | Descripción | Ejemplo |
|----------|----------|-------------|---------|
| **vectordb** | `QDRANT_URL` | URL del cluster de Qdrant Cloud | `https://abc.us-central1-0.gcp.cloud.qdrant.io:6333` |
| **vectordb** | `QDRANT_API_KEY` | API key de Qdrant Cloud | `your-api-key-keep-secret` |
| **vectordb** | `VECTOR_COLLECTION_NAME` | Colección principal | `holistic_memory` |
| **agents** | `AGENT_SERVICE_QDRANT_URL` | URL del cluster | `https://abc.us-central1-0.gcp.cloud.qdrant.io:6333` |
| **agents** | `AGENT_SERVICE_QDRANT_API_KEY` | API key | `your-api-key-keep-secret` |
| **agents** | `AGENT_SERVICE_VECTOR_COLLECTION` | Colección de agents | `holistic_agents` |

---

## 5. Seguridad en Producción

### 5.1 Google Secret Manager

**Crear secret para Qdrant API Key**:
```bash
# Crear secret
gcloud secrets create qdrant-api-key \
  --replication-policy="automatic" \
  --data-file=- <<EOF
your-qdrant-api-key-here
EOF

# Dar permisos a service accounts
gcloud secrets add-iam-policy-binding qdrant-api-key \
  --member="serviceAccount:vectordb@aura360.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding qdrant-api-key \
  --member="serviceAccount:agents@aura360.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 5.2 Kubernetes Secrets

```yaml
# infra/gcp/k8s/secrets/qdrant-credentials.yaml
apiVersion: v1
kind: Secret
metadata:
  name: qdrant-credentials
  namespace: aura360
type: Opaque
data:
  api-key: # Base64 encoded, se inyecta desde Secret Manager
```

### 5.3 Usar Secret en Deployments

```yaml
# vectordb deployment
env:
  - name: QDRANT_API_KEY
    valueFrom:
      secretKeyRef:
        name: qdrant-credentials
        key: api-key
```

---

## 6. Monitoreo y Debugging

### 6.1 Verificar Conexión

```bash
# Desde vectordb service
cd services/vectordb
source .env
python -c "
from qdrant_client import QdrantClient
import os
client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))
print(client.get_collections())
"
```

### 6.2 Ver Métricas en Qdrant Console

1. Ir a https://cloud.qdrant.io
2. Seleccionar tu cluster
3. Ver:
   - **Storage**: Uso de disco
   - **RAM**: Uso de memoria
   - **Requests**: Requests por segundo
   - **Latency**: P50, P95, P99

### 6.3 Logs de Servicios

```bash
# Logs de vectordb service
kubectl logs -n aura360 -l app=vectordb --tail=100 -f

# Logs de agents service
kubectl logs -n aura360 -l app=agents --tail=100 -f
```

---

## 7. Troubleshooting

### Problema: "Connection refused" al conectar a Qdrant

**Solución**:
1. Verificar que el cluster esté en estado "Running" en Qdrant Console
2. Verificar que la URL incluya el puerto `:6333`
3. Verificar que la API key sea correcta

```bash
# Test de conexión
curl -H "api-key: YOUR_API_KEY" \
  https://your-cluster.gcp.cloud.qdrant.io:6333/collections
```

---

### Problema: "Collection not found"

**Solución**:
1. Crear las colecciones necesarias

```bash
cd services/vectordb
python scripts/init_qdrant_collections.py
```

---

### Problema: "SSL Certificate verification failed"

**Solución**:
1. Asegúrate de que `AGENT_SERVICE_VECTOR_VERIFY_SSL=true` (para Qdrant Cloud)
2. Qdrant Cloud usa certificados válidos, **NO desactives SSL en producción**

---

## 8. Testing

### 8.1 Test de Integración Completo

```bash
# Ejecutar test end-to-end
./scripts/run_user_context_e2e.sh
```

### 8.2 Test Manual desde Frontend

1. Login en la app web
2. Ir a "Dashboard" → "Consejo Holístico"
3. Ingresar una pregunta (ej: "¿Qué debo comer hoy?")
4. Verificar que se reciba una respuesta

---

## 9. Próximos Pasos

- [x] Configurar Qdrant Cloud desde GCP Marketplace
- [x] Crear colecciones necesarias
- [x] Actualizar variables de entorno en todos los servicios
- [ ] Migrar datos existentes (si aplica)
- [ ] Configurar Google Secret Manager para API keys
- [ ] Actualizar Helm charts para Kubernetes
- [ ] Probar integración end-to-end
- [ ] Configurar monitoreo y alertas

---

## 10. Referencias

- [Qdrant Cloud Documentation](https://qdrant.tech/documentation/cloud/)
- [Qdrant Python Client](https://github.com/qdrant/qdrant-client)
- [Google Secret Manager](https://cloud.google.com/secret-manager/docs)
- [AURA360 Architecture Docs](../docs/architecture/)
