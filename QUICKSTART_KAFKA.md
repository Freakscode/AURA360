# AURA360 - Quick Start: Event-Driven Architecture con Kafka

**Guía rápida para desarrolladores** | Tiempo estimado: 30 minutos

---

## 🎯 Objetivo

Levantar el entorno de desarrollo local con Kafka y publicar/consumir tu primer evento.

---

## 📦 Paso 1: Levantar Infraestructura Local (5 min)

```bash
# Desde la raíz del proyecto
cd /path/to/AURA360

# Levantar Kafka + Qdrant + Redis + Schema Registry + Kafka UI
docker-compose -f docker-compose.dev.yml up -d

# Verificar que todo esté corriendo
docker ps

# Deberías ver:
# - aura360-kafka
# - aura360-zookeeper
# - aura360-schema-registry
# - aura360-kafka-ui
# - aura360-qdrant
# - aura360-redis
# - aura360-grobid
# - aura360-kafka-init (se detiene después de crear topics)
```

### Verificar Kafka UI

Abrir http://localhost:8090 en el navegador.

Deberías ver:
- Cluster: `aura360-local`
- Topics: 6 topics (`aura360.user.events`, `aura360.context.aggregated`, etc.)

---

## 🧪 Paso 2: Probar Publisher (10 min)

### 2.1 Instalar el módulo compartido

```bash
# En el servicio que vayas a usar (ejemplo: Django API)
cd services/api

# Agregar dependencia local
uv add ../shared

# Verificar instalación
uv run python -c "from messaging import EventPublisher; print('✅ OK')"
```

### 2.2 Crear script de prueba

Crear `services/api/test_kafka_publisher.py`:

```python
"""
Test script para publicar eventos a Kafka
"""

from messaging import EventPublisher, MoodCreatedEvent
import time

def main():
    print("🚀 Iniciando publisher de prueba...")

    # Crear publisher
    with EventPublisher() as publisher:
        # Crear evento
        event = MoodCreatedEvent.from_mood_entry(
            user_id="test-user-123",
            mood_data={
                "mood_score": 8,
                "tags": ["happy", "productive"],
                "notes": "Testing Kafka integration!",
                "created_at": "2025-01-07T10:00:00Z"
            },
            trace_id="test-trace-001"
        )

        print(f"📤 Publicando evento: {event.event_type}")
        print(f"   Event ID: {event.event_id}")
        print(f"   User ID: {event.user_id}")

        # Publicar
        publisher.publish(event)

        print("✅ Evento publicado exitosamente!")
        print("🔍 Ve a Kafka UI para verificar: http://localhost:8090")

if __name__ == "__main__":
    main()
```

### 2.3 Ejecutar

```bash
cd services/api
uv run python test_kafka_publisher.py
```

**Salida esperada:**
```
🚀 Iniciando publisher de prueba...
📤 Publicando evento: user.mood.created
   Event ID: 123e4567-e89b-12d3-a456-426614174000
   User ID: test-user-123
✅ Evento publicado exitosamente!
🔍 Ve a Kafka UI para verificar: http://localhost:8090
```

### 2.4 Verificar en Kafka UI

1. Ir a http://localhost:8090
2. Click en Topics → `aura360.user.events`
3. Click en Messages
4. Deberías ver tu evento con:
   - Key: `test-user-123`
   - Value: JSON con los datos del mood
   - Headers: `event_type`, `event_id`, `trace_id`

---

## 🎧 Paso 3: Probar Consumer (10 min)

### 3.1 Crear script consumer

Crear `services/vectordb/test_kafka_consumer.py`:

```python
"""
Test script para consumir eventos de Kafka
"""

from messaging import EventHandler, MoodCreatedEvent

def main():
    print("🎧 Iniciando consumer de prueba...")
    print("📥 Escuchando eventos en topic: aura360.user.events")
    print("   (Presiona Ctrl+C para detener)")
    print()

    # Crear handler con decorator
    handler = EventHandler(
        group_id="test-consumer-group",
        topics=["aura360.user.events"]
    )

    @handler.on("user.mood.created")
    def handle_mood_created(event: MoodCreatedEvent):
        print("=" * 60)
        print("📨 EVENTO RECIBIDO!")
        print(f"   Tipo: {event.event_type}")
        print(f"   Event ID: {event.event_id}")
        print(f"   User ID: {event.user_id}")
        print(f"   Trace ID: {event.trace_id}")
        print(f"   Mood Score: {event.data.get('mood_score')}")
        print(f"   Tags: {event.data.get('tags')}")
        print(f"   Notes: {event.data.get('notes')}")
        print("=" * 60)
        print()

    # Start consuming (blocking)
    try:
        handler.start()
    except KeyboardInterrupt:
        print("\n🛑 Consumer detenido por usuario")

if __name__ == "__main__":
    main()
```

### 3.2 Ejecutar consumer (en terminal separada)

```bash
# Terminal 2
cd services/vectordb
uv add ../shared  # Si aún no lo agregaste
uv run python test_kafka_consumer.py
```

**Salida esperada:**
```
🎧 Iniciando consumer de prueba...
📥 Escuchando eventos en topic: aura360.user.events
   (Presiona Ctrl+C para detener)

============================================================
📨 EVENTO RECIBIDO!
   Tipo: user.mood.created
   Event ID: 123e4567-e89b-12d3-a456-426614174000
   User ID: test-user-123
   Trace ID: test-trace-001
   Mood Score: 8
   Tags: ['happy', 'productive']
   Notes: Testing Kafka integration!
============================================================
```

### 3.3 Publicar más eventos

Vuelve a la Terminal 1 y ejecuta el publisher varias veces:

```bash
# Terminal 1
cd services/api
uv run python test_kafka_publisher.py
uv run python test_kafka_publisher.py
uv run python test_kafka_publisher.py
```

El consumer en Terminal 2 debería mostrar cada evento en tiempo real.

---

## 🔥 Paso 4: Test End-to-End Completo (5 min)

### 4.1 Flujo completo: Publisher → Consumer → Procesamiento

Crear `services/vectordb/test_e2e.py`:

```python
"""
Test end-to-end: Simula flujo completo de context aggregation
"""

from messaging import EventHandler, EventPublisher
from messaging import MoodCreatedEvent, ContextAggregatedEvent
import time

# Simular agregación de contexto
def aggregate_context(mood_event: MoodCreatedEvent) -> dict:
    """Simula agregación de contexto de usuario"""
    return {
        "user_id": mood_event.user_id,
        "mood_summary": {
            "recent_score": mood_event.data["mood_score"],
            "tags": mood_event.data["tags"]
        },
        "timestamp": time.time()
    }

def main():
    print("🧪 Test E2E: Mood Created → Context Aggregated")
    print()

    publisher = EventPublisher()

    # Setup consumer para mood events
    handler = EventHandler(
        group_id="e2e-test-aggregator",
        topics=["aura360.user.events"]
    )

    @handler.on("user.mood.created")
    def handle_mood(event: MoodCreatedEvent):
        print(f"✅ [1/3] Mood event recibido: user={event.user_id}")

        # Agregar contexto
        context_data = aggregate_context(event)
        print(f"✅ [2/3] Contexto agregado: {context_data}")

        # Publicar evento de contexto agregado
        context_event = ContextAggregatedEvent(
            user_id=event.user_id,
            trace_id=event.trace_id,
            context_data=context_data
        )
        publisher.publish(context_event)
        print(f"✅ [3/3] Context aggregated event publicado!")
        print()

    # Start
    print("📥 Consumer iniciado, esperando eventos...")
    print("   (Publica eventos con test_kafka_publisher.py)")
    print()
    handler.start()

if __name__ == "__main__":
    main()
```

### 4.2 Ejecutar

```bash
# Terminal 1: Consumer E2E
cd services/vectordb
uv run python test_e2e.py

# Terminal 2: Publisher
cd services/api
uv run python test_kafka_publisher.py
```

### 4.3 Verificar en Kafka UI

1. Ir a http://localhost:8090
2. Verificar messages en:
   - `aura360.user.events` → debería tener 1 mensaje nuevo
   - `aura360.context.aggregated` → debería tener 1 mensaje nuevo

---

## 📚 Paso 5: Próximos Pasos

### 5.1 Integrar en Django Views

```python
# services/api/holistic/views.py
from rest_framework.decorators import api_view
from messaging import publish_event, MoodCreatedEvent

@api_view(['POST'])
def create_mood_entry(request):
    # Guardar en Supabase
    mood_entry = save_to_database(request.data)

    # Publicar evento (¡reemplaza llamadas síncronas!)
    event = MoodCreatedEvent.from_mood_entry(
        user_id=request.user.id,
        mood_data=mood_entry,
        trace_id=request.headers.get('X-Trace-Id')
    )
    publish_event(event)

    return Response(mood_entry, status=201)
```

### 5.2 Integrar en Vectordb Service

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
def handle_context(event: ContextAggregatedEvent):
    # Vectorizar
    vectors = generate_embeddings(event.context_data)

    # Ingestar en Qdrant
    ingest_vectors(vectors, collection="user_context")

if __name__ == "__main__":
    handler.start()
```

### 5.3 Agregar al docker-compose

```yaml
# services/vectordb/docker-compose.yml (agregar)
vectordb-consumer:
  build:
    context: .
  depends_on:
    - kafka
    - qdrant
  environment:
    - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
    - QDRANT_URL=http://qdrant:6333
  command: ["python", "-m", "vectosvc.kafka.consumer"]
```

---

## 🐛 Troubleshooting

### Error: "No brokers available"

```bash
# Verificar que Kafka esté corriendo
docker ps | grep kafka

# Reiniciar Kafka
docker-compose -f docker-compose.dev.yml restart kafka

# Ver logs
docker logs aura360-kafka
```

### Error: "Topic does not exist"

```bash
# Listar topics
docker exec aura360-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Recrear topics
docker-compose -f docker-compose.dev.yml restart kafka-init

# O crear manualmente
docker exec aura360-kafka kafka-topics --bootstrap-server localhost:9092 \
  --create --topic aura360.user.events --partitions 3
```

### Consumer no recibe mensajes

1. Verificar en Kafka UI que el mensaje está en el topic
2. Verificar que el `event_type` en el header coincida con el handler
3. Verificar que el consumer group ID sea único
4. Revisar logs del consumer

### Ver todos los logs

```bash
# Todos los servicios
docker-compose -f docker-compose.dev.yml logs -f

# Solo Kafka
docker logs -f aura360-kafka

# Solo consumer (si está en Docker)
docker logs -f aura360-vectordb-consumer
```

---

## 📖 Recursos

- **Documentación shared/messaging**: `services/shared/README.md`
- **Confluent Docs**: https://docs.confluent.io/kafka-clients/python/current/
- **Event Schemas**: `services/shared/messaging/events.py`
- **Kafka UI**: http://localhost:8090
- **Architecture Doc**: Ver `CLAUDE.md` sección de Event-Driven Architecture

---

## ✅ Checklist de Verificación

Antes de continuar con desarrollo:

- [ ] Docker Compose levantado correctamente
- [ ] Kafka UI accesible en http://localhost:8090
- [ ] 6 topics visibles en Kafka UI
- [ ] Publisher test funciona
- [ ] Consumer test funciona
- [ ] E2E test funciona
- [ ] Mensajes visibles en Kafka UI

---

**🎉 ¡Listo! Ahora puedes empezar a integrar Kafka en tus servicios.**

**Siguiente paso**: Ver el plan detallado en el issue/documento de planificación para tu rol (Backend Dev, DevOps, Frontend).
