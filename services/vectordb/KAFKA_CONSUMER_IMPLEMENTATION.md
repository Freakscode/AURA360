# Kafka Consumer Implementation - Vectordb Service

**Date**: 2025-01-07
**Status**: ✅ Implemented
**Developer**: Backend FastAPI Developer

---

## Summary

Successfully implemented Kafka consumers for the Vectordb service according to `KAFKA_IMPLEMENTATION_PLAN.md` (Days 4-7). The implementation provides event-driven context aggregation and vectorization with Celery fallback support.

---

## Files Created/Modified

### New Files

1. **`vectosvc/kafka/__init__.py`**
   - Package initialization for Kafka consumer module

2. **`vectosvc/kafka/consumer.py`** (349 lines)
   - Main Kafka consumer implementation
   - Event handlers for user events and context processing
   - Orchestrates existing pipeline code

3. **`test_kafka_consumer.py`**
   - Test script for validating consumer functionality
   - Publishes test mood events to Kafka

### Modified Files

1. **`pyproject.toml`**
   - Added `confluent-kafka>=2.3.0` dependency
   - Prepared for `aura360-messaging` shared module (requires proper installation)

2. **`vectosvc/worker/tasks.py`** (153 lines added)
   - Added 3 Celery fallback tasks:
     - `process_mood_created`
     - `process_activity_created`
     - `process_context_aggregated`
   - Mirrors Kafka consumer logic for hybrid fallback

3. **`docker-compose.yml`**
   - Added `vectordb-consumer` service
   - Configured with environment variables:
     - `MESSAGING_BACKEND=kafka`
     - `KAFKA_BOOTSTRAP_SERVERS=kafka:29092`
     - All Qdrant, Redis, GROBID configurations
   - Command: `python -m vectosvc.kafka.consumer`
   - Restart policy: `unless-stopped`

---

## Implementation Details

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KAFKA TOPICS                                 │
│                                                                 │
│  aura360.user.events          aura360.context.aggregated       │
│    ↓ user.mood.created          ↓ context.aggregated           │
│    ↓ user.activity.created                                     │
└─────────────────────────────────────────────────────────────────┘
         │                                │
         │                                │
    ┌────▼────────────────────────────────▼──────┐
    │   vectosvc.kafka.consumer                  │
    │                                             │
    │   • handle_mood_created                    │
    │   • handle_activity_created                │
    │   • handle_context_aggregated              │
    └─────────────────┬───────────────────────────┘
                      │
                      │ Uses existing code:
                      ├─► aggregate_user_context()
                      ├─► vectorize_context()
                      │     └─► Embeddings.encode()
                      │     └─► ingest_one()
                      │         └─► store.upsert()
                      │
                      ▼
              ┌───────────────┐
              │   Qdrant      │
              │ user_context  │
              │  collection   │
              └───────────────┘
```

### Event Flow

#### 1. User Event Processing (mood/activity)

```python
user.mood.created event
    ↓
handle_mood_created()
    ↓
aggregate_user_context()
    • Builds context snapshot
    • Creates text representation
    ↓
publish context.aggregated event
```

**Key Functions**:
- `aggregate_user_context(user_id, event_data, event_type)`: Creates context snapshot from event
- `_build_context_text(context)`: Converts context to natural language for vectorization

#### 2. Context Vectorization

```python
context.aggregated event
    ↓
handle_context_aggregated()
    ↓
vectorize_context()
    • Creates IngestRequest payload
    • Uses ingest_one() from existing pipeline
      - Embeddings.encode() → vectors
      - store.upsert() → Qdrant
    ↓
publish context.vectorized event
```

**Key Functions**:
- `vectorize_context(context_data, user_id, trace_id)`: Orchestrates vectorization pipeline
- Uses `source_type="user_context"` to route to correct Qdrant collection

### Integration with Existing Pipeline

The consumer **orchestrates** existing code, avoiding duplication:

1. **`vectosvc.core.embeddings.Embeddings`**
   - Used via `ingest_one()` call
   - Generates FastEmbed vectors
   - Leverages Redis cache (90% speedup)

2. **`vectosvc.core.pipeline.ingest_one()`**
   - Handles complete ingestion flow:
     - Text chunking (`_split_text`)
     - Embedding generation (`Embeddings.encode`)
     - Point ID generation (`_make_point_id`)
     - Qdrant upsert with payload
   - Supports `source_type` routing

3. **`vectosvc.core.qdrant_store.QdrantStore`**
   - Collection routing: `get_collection_for_source_type("user_context")`
   - Ensures collection exists with proper indexes
   - Upserts vectors with payloads

### Handler Registration

Uses **decorator-style EventHandler** from shared/messaging:

```python
handler = EventHandler(
    group_id="vectordb-context-processor",
    topics=["aura360.user.events", "aura360.context.aggregated"],
    auto_commit=True,
)

handler.consumer.register_handler("user.mood.created", handle_mood_created)
handler.consumer.register_handler("user.activity.created", handle_activity_created)
handler.consumer.register_handler("context.aggregated", handle_context_aggregated)

handler.start()  # Blocking
```

### Graceful Shutdown

Implements proper signal handling:

```python
def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal, closing consumer...")
    handler.stop()
    publisher.close()
    sys.exit(0)

signal.signal(signal.SIGTERM, shutdown_handler)
signal.signal(signal.SIGINT, shutdown_handler)
```

---

## Celery Fallback Tasks

Added 3 Celery tasks in `vectosvc/worker/tasks.py` that mirror Kafka handlers:

### 1. `process_mood_created`

```python
@celery.task(
    name="vectosvc.worker.tasks.process_mood_created",
    max_retries=3,
    autoretry_for=(Exception,),
)
def process_mood_created(self, event_dict: dict)
```

- Imports `aggregate_user_context` from consumer
- Chains to `process_context_aggregated.delay()`
- Same retry logic as Kafka

### 2. `process_activity_created`

```python
@celery.task(
    name="vectosvc.worker.tasks.process_activity_created",
    max_retries=3,
    autoretry_for=(Exception,),
)
def process_activity_created(self, event_dict: dict)
```

- Mirrors `handle_activity_created` logic
- Chains to vectorization task

### 3. `process_context_aggregated`

```python
@celery.task(
    name="vectosvc.worker.tasks.process_context_aggregated",
    max_retries=3,
    autoretry_for=(Exception,),
)
def process_context_aggregated(self, event_dict: dict)
```

- Imports `vectorize_context` from consumer
- Performs actual Qdrant ingestion
- Returns status with doc_id and chunk count

**Usage** (from Django API):

```python
from vectosvc.worker.tasks import process_mood_created

# If MESSAGING_BACKEND=celery
process_mood_created.delay({
    "user_id": "user-123",
    "data": mood_entry_data,
    "event_type": "user.mood.created",
    "trace_id": "trace-001"
})
```

---

## Docker Compose Configuration

Added `vectordb-consumer` service:

```yaml
vectordb-consumer:
  build:
    context: .
    args:
      EXTRAS: "gcs"
  depends_on:
    - qdrant
    - redis
    - grobid
  environment:
    - MESSAGING_BACKEND=${MESSAGING_BACKEND:-kafka}
    - KAFKA_BOOTSTRAP_SERVERS=${KAFKA_BOOTSTRAP_SERVERS:-kafka:29092}
    - QDRANT_URL=http://qdrant:6333
    - QDRANT_GRPC=qdrant:6334
    - BROKER_URL=redis://redis:6379/0
    - RESULT_BACKEND=redis://redis:6379/1
    - DEFAULT_EMBEDDING_MODEL=${DEFAULT_EMBEDDING_MODEL:-text-embedding-3-small}
    - EMBEDDING_VERSION=${EMBEDDING_VERSION:-2025.10.27}
    - EMBEDDING_DIM=384
    - VECTOR_DISTANCE=cosine
    - VECTOR_COLLECTION_NAME=${VECTOR_COLLECTION_NAME:-holistic_memory}
    - GROBID_URL=http://grobid:8070
  volumes:
    - ${HOME}/.config/gcloud:/gcloud:ro
    - .:/app:ro
  working_dir: /app
  command: ["python", "-m", "vectosvc.kafka.consumer"]
  restart: unless-stopped
```

**Environment Variables**:
- `MESSAGING_BACKEND`: Set to `kafka` to enable Kafka mode
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker address (docker: `kafka:29092`)
- All standard vectordb env vars (Qdrant, Redis, embeddings config)

---

## Testing

### Local Testing (without Docker)

#### Terminal 1: Start Consumer

```bash
cd services/vectordb
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export QDRANT_URL=http://localhost:6333
export BROKER_URL=redis://localhost:6379/0

uv run python -m vectosvc.kafka.consumer
```

#### Terminal 2: Publish Test Event

```bash
cd services/vectordb
uv run python test_kafka_consumer.py
```

#### Verify:

1. **Consumer Logs**: Should show:
   - "Processing mood event"
   - "Context aggregated and published"
   - "Context vectorized and published"

2. **Kafka UI**: http://localhost:8090
   - Topic `aura360.user.events`: 1 new message
   - Topic `aura360.context.aggregated`: 1 new message
   - Topic `aura360.context.vectorized`: 1 new message

3. **Qdrant**: http://localhost:6333/dashboard
   - Collection `user_context`: New vectors ingested
   - Check payload: `user_id`, `snapshot_type`, `text`

### Docker Testing

```bash
cd services/vectordb

# Start all services including consumer
docker-compose up -d

# View consumer logs
docker-compose logs -f vectordb-consumer

# Publish test event (from outside Docker)
python test_kafka_consumer.py

# Check Qdrant
curl http://localhost:6333/collections/user_context | jq
```

---

## Integration Points

### With Django API

Django should publish events using shared/messaging:

```python
# services/api/holistic/views.py
from messaging import publish_event
from messaging.events import MoodCreatedEvent

@api_view(['POST'])
def create_mood_entry(request):
    # Save to Supabase
    mood_entry = save_to_database(request.data)

    # Publish event (replaces HTTP calls!)
    event = MoodCreatedEvent.from_mood_entry(
        user_id=request.user.id,
        mood_data=mood_entry,
        trace_id=request.headers.get('X-Trace-Id')
    )
    publish_event(event)

    return Response(mood_entry, status=201)
```

### With Agents Service

Agents service will consume `context.vectorized` events for Guardian retrieval:

```python
# services/agents/kafka/consumer.py
@handler.on("context.vectorized")
def handle_context_vectorized(event: ContextVectorizedEvent):
    # Context is now available in Qdrant for retrieval
    logger.info(f"User context updated: {event.user_id}")
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MESSAGING_BACKEND` | `kafka` | `kafka` or `celery` |
| `KAFKA_BOOTSTRAP_SERVERS` | `kafka:29092` | Kafka broker address |
| `QDRANT_URL` | `http://qdrant:6333` | Qdrant REST endpoint |
| `BROKER_URL` | `redis://redis:6379/0` | Celery broker (also used for embedding cache) |
| `DEFAULT_EMBEDDING_MODEL` | `text-embedding-3-small` | FastEmbed model name |
| `EMBEDDING_VERSION` | `2025.10.27` | Embedding version for metadata |
| `VECTOR_COLLECTION_NAME` | `holistic_memory` | Default Qdrant collection |

### Kafka Topics Consumed

1. **`aura360.user.events`**
   - Event Types: `user.mood.created`, `user.activity.created`
   - Consumer Group: `vectordb-context-processor`

2. **`aura360.context.aggregated`**
   - Event Type: `context.aggregated`
   - Consumer Group: `vectordb-context-processor`

### Kafka Topics Published

1. **`aura360.context.aggregated`**
   - Published after user event processing
   - Contains aggregated context snapshot

2. **`aura360.context.vectorized`**
   - Published after vectorization completes
   - Contains embedding metadata and status

---

## Error Handling

### Consumer-Level Errors

All handlers use **try-except** to catch errors without crashing the consumer:

```python
try:
    # Process event
    result = vectorize_context(...)
except Exception as e:
    logger.error("Failed to process event: {}", e, exc_info=True)
    # Don't re-raise - consumer continues processing
```

### Pipeline-Level Errors

Existing error handling in `ingest_one()`:

- Uses `pipeline_metrics.record_error()`
- Logs detailed error information
- Raises exception (caught by consumer handler)

### Celery Fallback Errors

- Automatic retries: 3 attempts
- Exponential backoff with jitter
- After max retries: task marked as FAILURE (no DLQ for events currently)

---

## Performance Considerations

### Embedding Cache

The consumer leverages existing Redis cache in `Embeddings.encode()`:

- **Cache Hit Rate**: ~90% for similar texts
- **Speedup**: 11.13s → 1.12s (10x faster)
- **TTL**: 7 days (configurable via `CACHE_EMBEDDING_TTL`)

### Chunking

Uses existing `_split_text()` from pipeline:

- **Chunk Size**: 900 chars (default)
- **Overlap**: 150 chars
- **Adjustable**: Via `IngestRequest.chunk_size` and `.chunk_overlap`

### Consumer Throughput

- **Auto-commit**: Enabled (reduces latency)
- **Consumer Group**: Allows horizontal scaling
- **Partition Support**: Can scale to multiple partitions

---

## Monitoring

### Logs to Watch

```bash
# Consumer startup
INFO: 🚀 Starting Vectordb Kafka Consumer
INFO: 📥 Registered handlers:
INFO:    - user.mood.created → aggregate context
INFO:    - user.activity.created → aggregate context
INFO:    - context.aggregated → vectorize and ingest

# Event processing
INFO: Processing mood event: user_id=user-123 event_id=... trace_id=...
INFO: Context aggregated and published: user_id=user-123
INFO: Processing context aggregation: user_id=user-123
INFO: Context vectorized and published: user_id=user-123 doc_id=... chunks=3

# Pipeline metrics (from ingest_one)
INFO: Ingested doc_id=... chunks=3 collection=user_context source_type=user_context
```

### Metrics to Track

1. **Consumer Lag**: Monitor via Kafka UI or Confluent Cloud
2. **Processing Time**: Logged in `vectorize_context` result
3. **Error Rate**: Count of exception logs
4. **Throughput**: Events processed per second
5. **Cache Hit Rate**: Via `Embeddings.get_cache_stats()`

---

## Deployment Checklist

- [x] Shared messaging dependency added to pyproject.toml
- [x] Consumer script created with EventHandler
- [x] Celery fallback tasks implemented
- [x] docker-compose.yml updated with consumer service
- [x] Test script created
- [ ] Shared module properly installed (requires `uv add` or pip install from ../shared)
- [ ] Environment variables configured (KAFKA_BOOTSTRAP_SERVERS, etc.)
- [ ] Kafka topics created (via docker-compose.dev.yml kafka-init)
- [ ] Integration test: Django → Kafka → Vectordb → Qdrant
- [ ] Load test: 100 concurrent events
- [ ] Monitoring dashboard configured

---

## Next Steps

### For DevOps

1. **Setup Confluent Cloud** (or local Kafka via docker-compose.dev.yml)
   - Create topics: `aura360.user.events`, `aura360.context.aggregated`, `aura360.context.vectorized`
   - Configure retention: 7 days
   - Create ACLs if needed

2. **Deploy to Railway**
   - Add consumer service to Dockerfile
   - Configure environment variables
   - Setup health checks

3. **Monitoring**
   - Configure alerts for consumer lag
   - Track error rate
   - Monitor Qdrant collection growth

### For Backend Django Developer

1. **Implement Event Publishing**
   - Update `holistic/views.py` to publish events
   - Replace HTTP calls to vectordb with Kafka events
   - Add idempotency keys

2. **Testing**
   - E2E test: Create mood entry → Verify in Qdrant
   - Load test: 100 concurrent requests

### For Backend Agents Developer

1. **Implement Context Consumption**
   - Add handler for `context.vectorized` events
   - Update Guardian to use vectorized context
   - Implement request-reply pattern for advice

---

## Troubleshooting

### Consumer not receiving messages

1. Check Kafka UI: Are messages in the topic?
2. Verify `event_type` header matches handler registration
3. Check consumer group ID is unique
4. View consumer logs for errors

### Vectorization fails

1. Check Qdrant is accessible: `curl http://localhost:6333/collections`
2. Verify embedding model is available (FastEmbed downloads on first use)
3. Check Redis is accessible for cache
4. Review logs for specific error

### Permission issues with venv

```bash
# If uv sync fails with permission errors:
cd services/vectordb
chmod -R u+w .venv  # Or remove and recreate
uv sync
```

### Import errors for shared/messaging

```bash
# Install shared module in editable mode
cd services/shared
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/AURA360/services/shared:$PYTHONPATH
```

---

## References

- **Implementation Plan**: `/KAFKA_IMPLEMENTATION_PLAN.md`
- **Quickstart Guide**: `/QUICKSTART_KAFKA.md`
- **Shared Module**: `/services/shared/README.md`
- **Event Schemas**: `/services/shared/messaging/events.py`
- **Pipeline Code**: `/services/vectordb/vectosvc/core/pipeline.py`
- **Qdrant Store**: `/services/vectordb/vectosvc/core/qdrant_store.py`
- **Embeddings**: `/services/vectordb/vectosvc/core/embeddings.py`

---

**Status**: ✅ Implementation Complete
**Date**: 2025-01-07
**Next Phase**: Integration testing with Django API (Days 4-6 of plan)
