# Kafka Quick Start Guide - AURA360

**Last Updated**: 2025-11-07
**For**: Backend Developers

---

## Quick Commands

### Start Kafka Local
```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360
docker compose -f docker-compose.dev.yml up -d
```

### Check Status
```bash
docker compose -f docker-compose.dev.yml ps
```

### View Logs
```bash
# All services
docker compose -f docker-compose.dev.yml logs -f

# Specific service
docker compose -f docker-compose.dev.yml logs -f kafka
```

### Stop Kafka
```bash
docker compose -f docker-compose.dev.yml down
```

### Stop and Remove Volumes (Clean Reset)
```bash
docker compose -f docker-compose.dev.yml down -v
```

---

## Service Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| **Kafka Broker** | `localhost:9092` | Producer/Consumer connections |
| **Kafka UI** | http://localhost:8090 | Visual topic exploration |
| **Schema Registry** | http://localhost:8081 | Avro schema management |
| **Zookeeper** | `localhost:2181` | Kafka coordination (internal) |
| **Qdrant** | http://localhost:6333 | Vector database |
| **Redis** | `localhost:6379` | Cache & Celery broker |
| **GROBID** | http://localhost:8070 | PDF processing |

---

## Topics Created

```
✅ aura360.user.events          - User actions (mood, activity, ikigai)
✅ aura360.context.aggregated   - Aggregated user context
✅ aura360.context.vectorized   - Vectorized context embeddings
✅ aura360.guardian.requests    - Guardian advice requests
✅ aura360.guardian.responses   - Guardian advice responses
✅ aura360.vectordb.ingest      - Documents for vector ingestion
```

**Configuration**: 3 partitions, 7-day retention, snappy compression

---

## Environment Setup

### 1. Copy .env.example
```bash
# Django API
cd services/api
cp .env.example .env

# Agents Service
cd services/agents
cp .env.example .env

# Vectordb Service
cd services/vectordb
cp .env.example .env
```

### 2. Configure for Local Development
Edit each `.env` file and uncomment these lines:
```env
# Use local Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Comment out Confluent Cloud settings
# KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-east-1.aws.confluent.cloud:9092
# KAFKA_SECURITY_PROTOCOL=SASL_SSL
```

---

## Test Kafka Connection (Python)

```bash
# Install confluent-kafka
pip install confluent-kafka

# Create test script
cat > /tmp/test_kafka.py <<'EOF'
from confluent_kafka import Producer

conf = {'bootstrap.servers': 'localhost:9092'}
producer = Producer(conf)

def delivery_report(err, msg):
    if err:
        print(f'❌ Error: {err}')
    else:
        print(f'✅ Message delivered to {msg.topic()} [{msg.partition()}]')

producer.produce('aura360.user.events',
                 value='{"test": "Hello Kafka"}',
                 callback=delivery_report)
producer.flush()
EOF

# Run test
python /tmp/test_kafka.py
```

**Expected Output**:
```
✅ Message delivered to aura360.user.events [0]
```

---

## Explore Topics in Kafka UI

1. Open http://localhost:8090
2. Click on cluster **aura360-local**
3. Click **Topics** in sidebar
4. Select a topic (e.g., `aura360.user.events`)
5. Click **Messages** tab
6. Click **Produce Message** to send test data

---

## Common Issues

### Issue: "Connection refused to localhost:9092"
**Solution**:
```bash
# Check if Kafka is running
docker compose -f docker-compose.dev.yml ps kafka

# If not healthy, check logs
docker compose -f docker-compose.dev.yml logs kafka

# Restart if needed
docker compose -f docker-compose.dev.yml restart kafka
```

### Issue: "Topic not found"
**Solution**:
```bash
# Check kafka-init logs
docker compose -f docker-compose.dev.yml logs kafka-init

# If topics weren't created, restart kafka-init
docker compose -f docker-compose.dev.yml up -d kafka-init
```

### Issue: "Kafka UI not loading"
**Solution**:
```bash
# Check health
curl http://localhost:8090/actuator/health

# Restart Kafka UI
docker compose -f docker-compose.dev.yml restart kafka-ui
```

---

## Development Workflow

### 1. Morning Startup
```bash
cd /Users/freakscode/Proyectos\ 2025/AURA360
docker compose -f docker-compose.dev.yml up -d
open http://localhost:8090
```

### 2. During Development
- Use Kafka UI to monitor messages
- Check consumer lag
- View message payloads
- Debug event flows

### 3. End of Day
```bash
# Optional: Stop services to free resources
docker compose -f docker-compose.dev.yml stop

# Or keep running (data persists in volumes)
```

---

## Next Steps

1. ✅ **Local Kafka Running**: You're here
2. 📚 **Learn Kafka Basics**: Complete Confluent Fundamentals (2h)
3. 🔧 **Build Shared Module**: Create `services/shared/messaging/`
4. 📝 **Implement Producers**: Django API publishes events
5. 📥 **Implement Consumers**: Vectordb/Agents consume events
6. 🧪 **Integration Testing**: End-to-end flow verification
7. 🚀 **Confluent Cloud**: Production deployment

---

## Documentation

- **Full Setup Report**: `KAFKA_SETUP_REPORT.md`
- **Implementation Plan**: `KAFKA_IMPLEMENTATION_PLAN.md`
- **Confluent Cloud Setup**: `CONFLUENT_CLOUD_SETUP.md`
- **MCP Server Setup**: `MCP_CONFLUENT_SETUP.md`

---

## Pro Tips

### Monitor Consumer Lag
```bash
# In Kafka UI: Consumers → Select group → View lag per partition
```

### View Message Schema
```bash
# In Kafka UI: Topics → Select topic → Messages → Click message → View JSON
```

### Reset Consumer Offset (Local Testing)
```bash
docker compose -f docker-compose.dev.yml exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group your-consumer-group \
  --reset-offsets --to-earliest --all-topics --execute
```

### Tail Logs in Real-Time
```bash
# All services with color-coded output
docker compose -f docker-compose.dev.yml logs -f | grep -i error

# Just Kafka
docker compose -f docker-compose.dev.yml logs -f kafka
```

---

**Need Help?**
- Check `KAFKA_SETUP_REPORT.md` for detailed info
- Review logs: `docker compose -f docker-compose.dev.yml logs`
- Open Kafka UI: http://localhost:8090
- Ask in team Slack/Discord

---

**Happy Kafka Development!** 🚀
