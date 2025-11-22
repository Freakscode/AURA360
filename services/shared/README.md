# AURA360 Shared Messaging Module

Módulo compartido para comunicación event-driven entre servicios usando Apache Kafka (Confluent).

**✨ Nuevo**: Soporte para modo híbrido Kafka/Celery con rollback sin downtime.

## Instalación

```bash
# En cada servicio (api, vectordb, agents)
cd services/api  # o vectordb, o agents
uv add ../shared
```

## Configuración

### Modo de Operación

El módulo soporta **3 modos** configurables via `MESSAGING_BACKEND`:

| Modo | Valor | Uso |
|------|-------|-----|
| **Kafka** (default) | `kafka` | Producción normal con Confluent Cloud |
| **Celery** (fallback) | `celery` | Rollback si Kafka tiene problemas |
| **Disabled** (testing) | `disabled` | Testing o emergencia temporal |

### Variables de Entorno

#### Modo Kafka (Default)

```bash
# Seleccionar backend
MESSAGING_BACKEND=kafka  # ← NUEVO

# Development (local)
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SCHEMA_REGISTRY_URL=http://localhost:8081
ENV=development

# Production (Confluent Cloud)
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
KAFKA_SCHEMA_REGISTRY_URL=https://psrc-xxxxx.confluent.cloud
KAFKA_API_KEY=your-api-key
KAFKA_API_SECRET=your-api-secret
ENV=production
```

#### Modo Celery (Fallback)

```bash
# Seleccionar backend
MESSAGING_BACKEND=celery  # ← Switch a Celery

# Celery configuration
BROKER_URL=redis://redis:6379/0
RESULT_BACKEND=redis://redis:6379/1
```

#### Modo Disabled (Testing)

```bash
# Seleccionar backend
MESSAGING_BACKEND=disabled  # ← Deshabilitar eventos

# No requiere otras variables
```

## Uso

### ⭐ Recomendado: Uso Híbrido (Backend-Agnostic)

**Usar `publish_event()` en lugar de `EventPublisher` directo** para soporte de rollback:

```python
from messaging import publish_event, MoodCreatedEvent  # ← API híbrida

# Crear evento
event = MoodCreatedEvent.from_mood_entry(
    user_id="user-123",
    mood_data={"mood_score": 7, "tags": ["happy"]}
)

# Publicar (usa Kafka o Celery según MESSAGING_BACKEND)
publish_event(event)  # ← Cambia automáticamente sin modificar código
```

**Ventajas**:
- ✅ Rollback Kafka → Celery sin cambios de código
- ✅ Testing más fácil (usar `MESSAGING_BACKEND=disabled`)
- ✅ Migración gradual (algunos servicios Kafka, otros Celery)

---

### Publishing Events (Método Directo - Solo Kafka)

```python
from messaging import EventPublisher, MoodCreatedEvent

# Crear publisher (solo Kafka)
publisher = EventPublisher()

# Crear evento
event = MoodCreatedEvent.from_mood_entry(
    user_id="user-123",
    mood_data={
        "mood_score": 7,
        "tags": ["happy", "productive"],
        "notes": "Great day at work!",
        "created_at": "2025-01-07T10:00:00Z"
    },
    trace_id="trace-abc"
)

# Publicar evento
publisher.publish(event)

# Flush pendientes antes de cerrar
publisher.flush()
```

### Publishing con Context Manager

```python
from messaging import EventPublisher, ActivityCreatedEvent

# Auto-flush on exit
with EventPublisher() as publisher:
    event = ActivityCreatedEvent(
        user_id="user-123",
        data={
            "activity_type": "running",
            "duration_minutes": 30,
            "calories": 300
        }
    )
    publisher.publish(event)
# Automáticamente hace flush al salir
```

### Consuming Events (Callback Style)

```python
from messaging import EventConsumer, MoodCreatedEvent

# Crear consumer
consumer = EventConsumer(
    group_id="vectordb-context-aggregator",
    topics=["aura360.user.events"]
)

# Registrar handler
def handle_mood_created(event: MoodCreatedEvent):
    print(f"User {event.user_id} created mood with score {event.data['mood_score']}")
    # Process event...

consumer.register_handler("user.mood.created", handle_mood_created)

# Start consuming (blocking)
consumer.start()
```

### Consuming Events (Decorator Style)

```python
from messaging import EventHandler, MoodCreatedEvent, ActivityCreatedEvent

# Crear handler con decorators
handler = EventHandler(
    group_id="my-service",
    topics=["aura360.user.events"]
)

@handler.on("user.mood.created")
def handle_mood(event: MoodCreatedEvent):
    print(f"Mood: {event.data['mood_score']}")

@handler.on("user.activity.created")
def handle_activity(event: ActivityCreatedEvent):
    print(f"Activity: {event.data['activity_type']}")

# Start (blocking)
handler.start()
```

## Event Types

### User Events

```python
from messaging import MoodCreatedEvent, ActivityCreatedEvent, IkigaiUpdatedEvent

# Mood entry created
event = MoodCreatedEvent.from_mood_entry(
    user_id="user-123",
    mood_data={"mood_score": 7, ...}
)

# Activity logged
event = ActivityCreatedEvent(
    user_id="user-123",
    data={"activity_type": "running", ...}
)

# IKIGAI profile updated
event = IkigaiUpdatedEvent(
    user_id="user-123",
    data={"passions": [...], "missions": [...]}
)
```

### Context Events

```python
from messaging import ContextAggregatedEvent, ContextVectorizedEvent

# Context aggregated
event = ContextAggregatedEvent(
    user_id="user-123",
    context_data={
        "mood_summary": {...},
        "activity_summary": {...}
    }
)

# Context vectorized
event = ContextVectorizedEvent(
    user_id="user-123",
    context_data={...},
    vectors=[[0.1, 0.2, ...], ...],
    embedding_model="text-embedding-3-small",
    embedding_version="2025.01.07"
)
```

### Guardian Events

```python
from messaging import GuardianRequestEvent, GuardianResponseEvent

# Request advice from Guardian
request = GuardianRequestEvent.create(
    user_id="user-123",
    guardian_type="mental",
    query="I'm feeling stressed lately",
    context={"mood_history": [...]}
)

# Guardian response
response = GuardianResponseEvent(
    user_id="user-123",
    guardian_type="mental",
    request_id=request.request_id,  # Correlation ID
    response="Based on your context...",
    confidence_score=0.85,
    retrieval_context=[...],
    processing_time_ms=1234.5
)
```

### Vectordb Events

```python
from messaging import VectordbIngestRequestedEvent

# Request ingestion
event = VectordbIngestRequestedEvent(
    user_id="user-123",
    collection_name="user_context",
    vectors=[[0.1, 0.2, ...]],
    payloads=[{"metadata": "..."}]
)
```

## Ejemplos por Servicio

### Django API (Publisher)

```python
# services/api/holistic/views.py
from rest_framework.decorators import api_view
from messaging import publish_event, MoodCreatedEvent

@api_view(['POST'])
def create_mood_entry(request):
    # Guardar en Supabase
    mood_entry = save_to_database(request.data)

    # Publicar evento
    event = MoodCreatedEvent.from_mood_entry(
        user_id=request.user.id,
        mood_data=mood_entry
    )
    publish_event(event)

    return Response(mood_entry, status=201)
```

### Vectordb Service (Consumer)

```python
# services/vectordb/vectosvc/kafka/consumer.py
from messaging import EventHandler, ContextAggregatedEvent
from vectosvc.core.embeddings import generate_embeddings
from vectosvc.core.qdrant_store import ingest_vectors

handler = EventHandler(
    group_id="vectordb-vectorization",
    topics=["aura360.context.aggregated"]
)

@handler.on("context.aggregated")
def handle_context_aggregated(event: ContextAggregatedEvent):
    # Vectorizar contexto
    vectors = generate_embeddings(event.context_data)

    # Ingestar en Qdrant
    ingest_vectors(vectors, collection="user_context")

    # Publicar evento de completado
    # ...

if __name__ == "__main__":
    handler.start()
```

### Agents Service (Request-Reply Pattern)

```python
# services/agents/kafka/consumer.py
from messaging import EventHandler, GuardianRequestEvent, GuardianResponseEvent
from messaging import publish_event
from services.holistic import run_guardian

handler = EventHandler(
    group_id="agents-guardians",
    topics=["aura360.guardian.requests"]
)

@handler.on("guardian.request")
def handle_guardian_request(event: GuardianRequestEvent):
    # Ejecutar Guardian
    response_text = run_guardian(
        guardian_type=event.guardian_type,
        query=event.query,
        context=event.context
    )

    # Publicar respuesta
    response = GuardianResponseEvent(
        user_id=event.user_id,
        guardian_type=event.guardian_type,
        request_id=event.request_id,  # Correlation!
        response=response_text,
        confidence_score=0.9,
        retrieval_context=[],
        processing_time_ms=1500.0
    )
    publish_event(response)

if __name__ == "__main__":
    handler.start()
```

## Testing

```bash
# Run tests
cd services/shared
uv run pytest

# With coverage
uv run pytest --cov=messaging --cov-report=html
```

## Debugging

### Ver eventos en Kafka UI

1. Abrir http://localhost:8090
2. Navegar a Topics → `aura360.user.events`
3. Ver messages en tiempo real

### Logs

```python
import logging

# Habilitar logs de Kafka
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("messaging")
logger.setLevel(logging.DEBUG)
```

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                   KAFKA / CONFLUENT CLOUD                   │
│                                                             │
│  Topics:                                                    │
│   - aura360.user.events                                     │
│   - aura360.context.aggregated                              │
│   - aura360.context.vectorized                              │
│   - aura360.guardian.requests                               │
│   - aura360.guardian.responses                              │
│   - aura360.vectordb.ingest                                 │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐         ┌─────▼─────┐       ┌─────▼─────┐
    │ Django  │         │  Agents   │       │ Vectordb  │
    │   API   │         │  Service  │       │  Service  │
    │         │         │           │       │           │
    │ Publish │         │ Pub/Sub   │       │  Consume  │
    └─────────┘         └───────────┘       └───────────┘
```

## Mejores Prácticas

### 1. Usar Context Managers

```python
# ✅ Bueno
with EventPublisher() as publisher:
    publisher.publish(event)

# ❌ Malo
publisher = EventPublisher()
publisher.publish(event)
# Puede perder mensajes si se cierra abruptamente
```

### 2. Incluir Trace IDs

```python
# Para distributed tracing
event = MoodCreatedEvent.from_mood_entry(
    user_id="user-123",
    mood_data={...},
    trace_id=request.headers.get("X-Trace-Id")  # Propagar de request
)
```

### 3. Manejar Errores en Handlers

```python
@handler.on("user.mood.created")
def handle_mood(event: MoodCreatedEvent):
    try:
        process_mood(event)
    except Exception as e:
        logger.error(f"Failed to process mood: {e}")
        # Considerar publicar a DLQ (Dead Letter Queue)
```

### 4. Graceful Shutdown

```python
import signal

handler = EventHandler(...)

def signal_handler(sig, frame):
    print("Shutting down...")
    handler.stop()

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

handler.start()
```

## Troubleshooting

### Error: "Topic does not exist"

```bash
# Verificar topics en Kafka UI: http://localhost:8090
# O crear manualmente:
docker exec aura360-kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic aura360.user.events --partitions 3
```

### Error: "No brokers available"

- Verificar que Kafka está corriendo: `docker ps | grep kafka`
- Verificar `KAFKA_BOOTSTRAP_SERVERS` en env

### Consumer Lag alto

- Aumentar número de consumers (scale horizontally)
- Aumentar partitions del topic
- Optimizar handler logic

## Próximos Pasos

1. **Schema Registry**: Usar Avro para schemas tipados
2. **Dead Letter Queue**: Manejar eventos fallidos
3. **Metrics**: Integrar Prometheus para monitoring
4. **Streaming**: Implementar Kafka Streams para procesamiento complejo
