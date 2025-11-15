# Guardian Request-Reply Pattern via Kafka

**Implementation Date**: 2025-11-07
**Status**: ✅ Complete
**Pattern**: Asynchronous Request-Reply with Correlation IDs

---

## Overview

This document describes the implementation of the Guardian request-reply pattern using Apache Kafka for event-driven communication between the AURA360 API and Agents Service.

### Architecture

```
┌─────────────────┐
│   API Service   │
│ (FastAPI)       │
└────────┬────────┘
         │ 1. POST /advice/async
         │    (publish GuardianRequestEvent)
         ▼
┌─────────────────────────────────────┐
│  Kafka: aura360.guardian.requests   │
└────────┬────────────────────────────┘
         │ 2. Consumer polls
         ▼
┌─────────────────┐
│ Guardian        │
│ Consumer        │
│ (handlers.py)   │
└────────┬────────┘
         │ 3. Process with HolisticAdviceService
         │    (uses existing Guardian logic)
         ▼
┌─────────────────────────────────────┐
│  Kafka: aura360.guardian.responses  │
└────────┬────────────────────────────┘
         │ 4. Response consumer polls
         ▼
┌─────────────────┐
│    Redis        │
│  (TTL: 30 min)  │
└────────┬────────┘
         │ 5. GET /advice/async/{request_id}
         │    (poll for response)
         ▼
┌─────────────────┐
│   API Service   │
│   Returns to    │
│     Client      │
└─────────────────┘
```

---

## Implementation Components

### 1. Dependencies Added

**File**: `/services/agents/pyproject.toml`

```toml
dependencies = [
    ...
    "confluent-kafka>=2.3.0",
    "redis>=5.0.0",
]
```

### 2. Kafka Consumer (Request Handler)

**File**: `/services/agents/kafka/consumer.py`

- **Purpose**: Listens to `aura360.guardian.requests` topic
- **Processes**: GuardianRequestEvent
- **Executes**: Existing Guardian logic via `HolisticAdviceService`
- **Publishes**: GuardianResponseEvent to `aura360.guardian.responses`

**Key Features**:
- Graceful shutdown (SIGTERM/SIGINT)
- Error handling with logging
- Automatic offset management
- Idempotent processing

**Usage**:
```bash
cd services/agents
python -m kafka.consumer
```

### 3. Request Handler Logic

**File**: `/services/agents/kafka/handlers.py`

**Class**: `GuardianRequestHandler`

**Workflow**:
1. Receives `GuardianRequestEvent` from consumer
2. Maps `guardian_type` (mental/physical/spiritual/holistic) to category (mind/body/soul/holistic)
3. Builds `AdviceRequest` using existing service
4. Executes `HolisticAdviceService.generate_advice()`
5. Extracts response data (summary, recommendations, retrieval context)
6. Builds `GuardianResponseEvent` with **correlation ID** (`request_id`)
7. Publishes response to `aura360.guardian.responses`

**Error Handling**:
- `ServiceError`: Publishes error response with error details
- `Exception`: Publishes generic error response
- All errors include correlation ID for tracking

### 4. Response Consumer (Redis Storage)

**File**: `/services/agents/kafka/response_consumer.py`

- **Purpose**: Listens to `aura360.guardian.responses` topic
- **Stores**: Responses in Redis with TTL (default 30 minutes)
- **Key Format**: `guardian:response:{request_id}`

**Usage**:
```bash
cd services/agents
python -m kafka.response_consumer
```

### 5. Async API Endpoints

**File**: `/services/agents/api/routers/holistic.py`

#### Endpoint 1: Submit Async Request

**POST** `/api/v1/holistic/advice/async`

**Request Body**:
```json
{
  "trace_id": "trace-123",
  "category": "mind",
  "user_id": "user-456",
  "query": "¿Cómo manejar el estrés?",
  "context": {
    "user_profile": {
      "id": "user-456",
      "name": "Ana",
      "age": 30
    },
    "preferences": {
      "focus": ["mindfulness"]
    }
  }
}
```

**Response** (202 Accepted):
```json
{
  "status": "accepted",
  "request_id": "uuid-789",
  "message": "Solicitud aceptada y en procesamiento",
  "poll_url": "/api/v1/holistic/advice/async/uuid-789",
  "meta": {
    "trace_id": "trace-123",
    "timestamp": "2025-11-07T12:00:00Z"
  }
}
```

#### Endpoint 2: Poll for Response

**GET** `/api/v1/holistic/advice/async/{request_id}?timeout=10`

**Query Parameters**:
- `timeout` (optional): Wait time in seconds (0-30, default=0)

**Response States**:

**Pending** (202 Accepted):
```json
{
  "status": "pending",
  "request_id": "uuid-789",
  "message": "La solicitud está en procesamiento"
}
```

**Completed** (200 OK):
```json
{
  "status": "completed",
  "request_id": "uuid-789",
  "data": {
    "event_type": "guardian.response",
    "request_id": "uuid-789",
    "response": "Aquí está tu plan personalizado...",
    "recommendations": [...],
    "confidence_score": 0.85,
    "retrieval_context": [...],
    "processing_time_ms": 3456.78
  }
}
```

---

## Correlation ID Pattern

### How Correlation IDs Work

1. **Request Generation**:
   - API generates unique `request_id` (UUID)
   - Included in `GuardianRequestEvent`
   - Returned to client for polling

2. **Request Processing**:
   - Consumer extracts `request_id` from event
   - Passes through entire processing pipeline
   - Included in all log messages for tracing

3. **Response Correlation**:
   - `GuardianResponseEvent` includes same `request_id`
   - Response consumer uses `request_id` as Redis key
   - API polls Redis using client's `request_id`

4. **Guaranteed Matching**:
   - Kafka message keys use `request_id`
   - Kafka headers include `request_id`
   - Redis keys namespace: `guardian:response:{request_id}`

### Correlation Flow Diagram

```
Client Request
     │
     ├─ request_id: "abc-123"
     │
     ▼
API: GuardianRequestEvent
     │
     ├─ request_id: "abc-123"  ← Propagated
     │
     ▼
Kafka: aura360.guardian.requests
     │
     ├─ key: "abc-123"
     ├─ headers.request_id: "abc-123"
     │
     ▼
Consumer: GuardianRequestHandler
     │
     ├─ Processes with request_id: "abc-123"
     │
     ▼
Kafka: aura360.guardian.responses
     │
     ├─ request_id: "abc-123"  ← Correlated
     ├─ key: "abc-123"
     ├─ headers.request_id: "abc-123"
     │
     ▼
Redis: guardian:response:abc-123  ← Stored
     │
     ▼
API: GET /advice/async/abc-123    ← Polled
     │
     ▼
Client: Receives correlated response
```

---

## Testing

### Prerequisites

1. **Kafka**: Running at `localhost:9092`
2. **Redis**: Running at `localhost:6379`
3. **Qdrant**: Running at `localhost:6333` (for vector retrieval)
4. **Environment Variables**:
   ```bash
   KAFKA_BOOTSTRAP_SERVERS=localhost:9092
   REDIS_URL=redis://localhost:6379/0
   AGENT_SERVICE_QDRANT_URL=http://localhost:6333
   GOOGLE_API_KEY=your-api-key
   ```

### Start Services

**Terminal 1**: Start Guardian Request Consumer
```bash
cd services/agents
uv sync
uv run python -m kafka.consumer
```

**Terminal 2**: Start Guardian Response Consumer
```bash
cd services/agents
uv run python -m kafka.response_consumer
```

**Terminal 3**: Start FastAPI Server
```bash
cd services/agents
uv run uvicorn main:app --reload --port 8080
```

### Run Test Script

**Terminal 4**: Execute Test
```bash
cd services/agents
uv run python scripts/test_guardian_kafka_flow.py
```

### Test Output

```
================================================================================
AURA360 Guardian Kafka Request-Reply Flow Test
================================================================================

Prerequisites:
  1. Kafka running at localhost:9092
  2. Redis running at localhost:6379
  3. Guardian consumer running: python -m kafka.consumer
  4. Response consumer running: python -m kafka.response_consumer

Starting test in 3 seconds...

--- Test 1: Mental Guardian ---
2025-11-07 12:00:00 - INFO - Starting request-reply flow test
2025-11-07 12:00:00 - INFO - Step 1: Publishing GuardianRequestEvent...
2025-11-07 12:00:00 - INFO - Published GuardianRequestEvent
2025-11-07 12:00:01 - INFO - Step 2: Polling for GuardianResponseEvent from Kafka...
2025-11-07 12:00:05 - INFO - Received matching GuardianResponseEvent
2025-11-07 12:00:05 - INFO - Step 3: Checking Redis for stored response...
2025-11-07 12:00:05 - INFO - Found response in Redis
2025-11-07 12:00:05 - INFO - ✓ Request-reply flow test PASSED

Results:
  Success: True
  Correlation Verified: True
  Total Time: 5234.56ms
  Response Summary: Aquí está tu plan personalizado para manejar el estrés laboral...

--- Test 2: Physical Guardian ---
...

================================================================================
Test Summary
================================================================================
  Test 1 (Mental): ✓ PASSED
  Test 2 (Physical): ✓ PASSED

  Overall: ✓ ALL TESTS PASSED
================================================================================
```

---

## Error Handling

### Consumer Errors

1. **JSON Decode Errors**:
   - Logged with message details
   - Message committed (skipped)
   - Does not crash consumer

2. **Service Errors**:
   - Caught by handler
   - Error response published to Kafka
   - Client receives error response

3. **Kafka Connection Errors**:
   - Consumer retries automatically
   - Logged for monitoring
   - Graceful shutdown on SIGTERM

### API Errors

1. **Kafka Publishing Failures**:
   - Returns 500 Internal Server Error
   - Includes error message
   - Logged for debugging

2. **Redis Connection Errors**:
   - Returns 500 Internal Server Error
   - Polling continues for other requests

### Redis TTL Expiration

- Responses expire after 30 minutes (configurable)
- Client receives 202 Pending if expired
- Consumer group offset allows replay if needed

---

## Performance Considerations

### Latency

**Expected Latency**:
- **Publish**: <100ms
- **Processing**: 3-8 seconds (depending on Guardian complexity)
- **Redis Storage**: <50ms
- **Total**: 3-10 seconds

**Optimization**:
- Consumer uses `enable.auto.commit=True` (5s interval)
- Producer uses `acks=all` for reliability
- Redis TTL prevents memory bloat

### Throughput

**Current Capacity**:
- Single consumer: ~10-20 requests/min
- Parallel processing limited by Guardian LLM calls

**Scaling**:
- Add more consumer instances (same consumer group)
- Kafka partitions enable horizontal scaling
- Redis cluster for response storage

---

## Monitoring

### Key Metrics

1. **Kafka Consumer Lag**:
   - Monitor: `kafka-consumer-groups --describe`
   - Alert if lag > 100 messages

2. **Processing Time**:
   - Tracked in `processing_time_ms` field
   - Alert if > 30 seconds

3. **Redis Hit Rate**:
   - Monitor `INFO stats` command
   - Alert if response storage fails

4. **Correlation Errors**:
   - Monitor logs for "No handler registered"
   - Alert if request_id mismatches occur

### Logging

All components include structured logging with:
- `request_id`: Correlation ID
- `trace_id`: Distributed tracing
- `user_id`: User identifier
- `guardian_type`: Guardian category

---

## Deployment

### Docker Compose (Development)

```yaml
services:
  guardian-consumer:
    build: ./services/agents
    command: python -m kafka.consumer
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - REDIS_URL=redis://redis:6379/0
      - AGENT_SERVICE_QDRANT_URL=http://qdrant:6333
    depends_on:
      - kafka
      - redis
      - qdrant

  guardian-response-consumer:
    build: ./services/agents
    command: python -m kafka.response_consumer
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - kafka
      - redis
```

### Railway (Production)

1. **Service 1**: `agents-api` (FastAPI)
   - Command: `uvicorn main:app --host 0.0.0.0 --port 8080`

2. **Service 2**: `guardian-consumer`
   - Command: `python -m kafka.consumer`

3. **Service 3**: `guardian-response-consumer`
   - Command: `python -m kafka.response_consumer`

**Environment Variables**:
- `KAFKA_BOOTSTRAP_SERVERS`: Confluent Cloud endpoint
- `KAFKA_API_KEY`: Confluent Cloud API key
- `KAFKA_API_SECRET`: Confluent Cloud API secret
- `REDIS_URL`: Railway Redis URL
- `AGENT_SERVICE_QDRANT_URL`: Qdrant endpoint

---

## Future Enhancements

### 1. Streaming Responses

Implement `GuardianResponseChunkEvent` for real-time streaming:
- Client subscribes to WebSocket
- Guardian publishes chunks as they're generated
- Lower perceived latency

### 2. Dead Letter Queue (DLQ)

Add DLQ for failed messages:
- Consumer retries 3 times
- Failed messages moved to `aura360.guardian.requests.dlq`
- Manual review and replay

### 3. Metrics Dashboard

Integrate with Confluent Cloud Metrics:
- Consumer lag graphs
- Message throughput
- Error rates

### 4. Circuit Breaker

Add circuit breaker for Guardian failures:
- Open after 5 consecutive failures
- Half-open after 1 minute
- Prevents cascading failures

---

## Troubleshooting

### Consumer Not Processing Messages

**Symptom**: Messages published but no responses

**Checks**:
1. Consumer running: `ps aux | grep kafka.consumer`
2. Consumer logs: Check for errors
3. Kafka topics: `kafka-topics --list`
4. Consumer group: `kafka-consumer-groups --describe --group aura360-guardian-consumer`

**Fix**:
```bash
# Reset consumer group offset
kafka-consumer-groups --reset-offsets --to-earliest \
  --group aura360-guardian-consumer \
  --topic aura360.guardian.requests --execute
```

### Responses Not Stored in Redis

**Symptom**: Kafka response received but Redis empty

**Checks**:
1. Response consumer running
2. Redis connection: `redis-cli PING`
3. Response consumer logs

**Fix**:
```bash
# Restart response consumer
pkill -f response_consumer
python -m kafka.response_consumer
```

### Correlation ID Mismatch

**Symptom**: Client polls but receives wrong response

**Checks**:
1. Log `request_id` throughout pipeline
2. Verify Kafka message headers
3. Check Redis key format

**Fix**:
- Ensure `request_id` is UUID (unique)
- Verify producer sets correct headers
- Check handler propagates `request_id`

---

## References

- **Kafka Request-Reply Pattern**: https://www.confluent.io/blog/request-reply-pattern-apache-kafka/
- **Confluent Python Client**: https://docs.confluent.io/kafka-clients/python/current/
- **Event-Driven Architecture**: KAFKA_IMPLEMENTATION_PLAN.md
- **Guardian Routing**: GUARDIAN_ROUTING.md

---

**Author**: Backend Agents Developer
**Last Updated**: 2025-11-07
**Version**: 1.0
