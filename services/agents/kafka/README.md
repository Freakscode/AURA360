# Guardian Kafka Integration

Event-driven communication module for AURA360 Guardian requests and responses.

## Overview

This module implements the request-reply pattern using Apache Kafka:
- **consumer.py**: Processes GuardianRequestEvent and publishes responses
- **response_consumer.py**: Stores responses in Redis for API polling
- **handlers.py**: Business logic for processing Guardian requests

## Quick Start

### 1. Install Dependencies

```bash
cd services/agents
uv sync
```

### 2. Start Consumers

**Terminal 1**: Request Consumer
```bash
uv run python -m kafka.consumer
```

**Terminal 2**: Response Consumer
```bash
uv run python -m kafka.response_consumer
```

### 3. Test

```bash
uv run python scripts/test_guardian_kafka_flow.py
```

## Architecture

```
API → Kafka (requests) → Consumer → Kafka (responses) → Redis → API
```

## Environment Variables

```bash
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379/0
AGENT_SERVICE_QDRANT_URL=http://localhost:6333
GOOGLE_API_KEY=your-api-key
```

## Topics

- **aura360.guardian.requests**: Incoming Guardian requests
- **aura360.guardian.responses**: Outgoing Guardian responses

## Correlation ID

All requests include a `request_id` (UUID) for correlation:
- Request event includes `request_id`
- Response event includes same `request_id`
- Redis stores responses with key: `guardian:response:{request_id}`
- API polls Redis using `request_id`

## Documentation

See [GUARDIAN_KAFKA_REQUEST_REPLY.md](../GUARDIAN_KAFKA_REQUEST_REPLY.md) for complete documentation.
