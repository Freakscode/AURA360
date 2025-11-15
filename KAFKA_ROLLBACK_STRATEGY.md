# AURA360 - Estrategia de Rollback: Kafka ↔ Celery

**Propósito**: Poder desactivar Kafka y volver a Celery sin downtime ni cambios de código.

---

## 🎯 Diseño: Arquitectura Híbrida

### Abstracción de Messaging

```python
# services/shared/messaging/backend.py

# ✅ Backend determinado por ENV VAR
MESSAGING_BACKEND = "kafka"  # o "celery" o "disabled"

# Código de aplicación NO cambia:
from messaging import publish_event, MoodCreatedEvent

event = MoodCreatedEvent.from_mood_entry(...)
publish_event(event)  # ← Usa Kafka o Celery según configuración
```

### Flujo

```
┌─────────────────────────────────────────────────────┐
│  Application Code (Django, Vectordb, Agents)        │
│                                                     │
│  from messaging import publish_event                │
│  publish_event(event)  ← API NO CAMBIA             │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │ Backend Selector  │
         │ (backend.py)      │
         └─────────┬─────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼─────┐        ┌─────▼──────┐
   │  Kafka   │        │   Celery   │
   │ Backend  │        │  Backend   │
   └──────────┘        └────────────┘
```

---

## 🔄 Modos de Operación

### Modo 1: Kafka (Default)

```bash
# .env
MESSAGING_BACKEND=kafka
KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.confluent.cloud:9092
KAFKA_API_KEY=xxx
KAFKA_API_SECRET=xxx
```

**Comportamiento**:
- ✅ Eventos se publican a Kafka
- ✅ Consumers leen de Kafka
- ✅ Celery solo para batch jobs (PDF processing)

---

### Modo 2: Celery (Fallback)

```bash
# .env
MESSAGING_BACKEND=celery
BROKER_URL=redis://redis:6379/0
RESULT_BACKEND=redis://redis:6379/1
```

**Comportamiento**:
- ✅ Eventos se convierten a Celery tasks
- ✅ Workers procesan via Celery
- ❌ Kafka NO se usa

**Mapping automático**:
```python
# Event → Celery Task
user.mood.created → vectosvc.worker.tasks.process_mood_created.delay(event)
context.aggregated → vectosvc.worker.tasks.process_context_aggregated.delay(event)
```

---

### Modo 3: Disabled (Testing/Emergency)

```bash
# .env
MESSAGING_BACKEND=disabled
```

**Comportamiento**:
- ⚠️ Eventos se loggean pero NO se procesan
- ⚠️ Solo para testing o emergencias temporales
- ⚠️ Funcionalidad asíncrona deshabilitada

---

## 🚨 Escenarios de Rollback

### Escenario 1: Kafka Down (Producción)

**Síntomas**:
- Errores de conexión a Confluent Cloud
- Consumer lag creciendo indefinidamente
- Timeouts en publicación de eventos

**Acción Inmediata** (2 minutos):

```bash
# 1. Cambiar a Celery en Railway (todos los servicios)
railway variables set MESSAGING_BACKEND=celery

# 2. Restart services
railway service restart api
railway service restart vectordb-api
railway service restart vectordb-worker
railway service restart agents

# 3. Verificar logs
railway logs api --tail=100
```

**Resultado**:
- ✅ Sistema funciona con Celery
- ✅ Sin downtime percibido por usuarios
- ⚠️ Pierdes eventos que estaban en Kafka (ver recovery más abajo)

---

### Escenario 2: Bugs en Consumers de Kafka

**Síntomas**:
- Consumer lag alto pero Kafka funciona
- Eventos procesados incorrectamente
- Loops infinitos en consumers

**Acción Gradual** (10 minutos):

```bash
# 1. Deshabilitar solo UN consumer problemático
# Ejemplo: vectordb-consumer tiene bug

# En Railway: vectordb-consumer service
MESSAGING_BACKEND=disabled  # Deshabilita solo este consumer

# 2. Fix bug en código
git commit -m "fix: vectordb consumer bug"
git push

# 3. Re-deploy consumer
railway up --service vectordb-consumer

# 4. Re-habilitar
MESSAGING_BACKEND=kafka
```

**Resultado**:
- ✅ Otros consumers siguen funcionando
- ✅ Bug fijado sin afectar todo el sistema

---

### Escenario 3: Confluent Cloud Quota Exceeded

**Síntomas**:
- "Quota exceeded" errors en Confluent Cloud
- Rate limiting en API calls
- Consumers throttled

**Acción** (5 minutos):

```bash
# Opción A: Upgrade Confluent tier (si presupuesto permite)
# → Ir a Confluent Cloud → Billing → Upgrade

# Opción B: Rollback a Celery temporalmente
railway variables set MESSAGING_BACKEND=celery

# Investigar causa:
# - ¿Productor en loop?
# - ¿Más tráfico de lo esperado?
# - ¿Retries excesivos?
```

---

### Escenario 4: Año Gratis Terminó (Post 12 meses)

**Planeado** (1 semana antes):

```bash
# Decisión 1: Pagar Confluent Cloud ($1,100/mes)
# → Solo si revenue justifica

# Decisión 2: Self-host Kafka en Railway
# → Ver KAFKA_SELF_HOSTED.md (crear documento aparte)

# Decisión 3: Rollback permanente a Celery
MESSAGING_BACKEND=celery

# Actualizar CLAUDE.md:
# "Sistema usa Celery para event processing,
#  Kafka se usó durante primeros 12 meses"
```

---

## 🔧 Implementación Técnica

### 1. Actualizar Django Views

**Antes** (acoplado a Kafka):
```python
# services/api/holistic/views.py
from messaging import EventPublisher, MoodCreatedEvent

publisher = EventPublisher()

@api_view(['POST'])
def create_mood_entry(request):
    mood_entry = save_to_database(request.data)

    event = MoodCreatedEvent.from_mood_entry(...)
    publisher.publish(event)  # ← Acoplado a Kafka

    return Response(mood_entry, status=201)
```

**Después** (híbrido):
```python
# services/api/holistic/views.py
from messaging import publish_event, MoodCreatedEvent  # ← Función abstracta

@api_view(['POST'])
def create_mood_entry(request):
    mood_entry = save_to_database(request.data)

    event = MoodCreatedEvent.from_mood_entry(...)
    publish_event(event)  # ← Usa Kafka o Celery según MESSAGING_BACKEND

    return Response(mood_entry, status=201)
```

---

### 2. Crear Celery Tasks (Fallback)

```python
# services/vectordb/vectosvc/worker/tasks.py
from celery import shared_task
from messaging.events import deserialize_event

@shared_task(name="vectosvc.worker.tasks.process_mood_created")
def process_mood_created(event_dict: dict):
    """
    Fallback Celery task for user.mood.created event

    Solo se ejecuta si MESSAGING_BACKEND=celery
    """
    from vectosvc.core.context_aggregation import aggregate_context

    # Deserialize event
    event = deserialize_event("user.mood.created", event_dict)

    # Process (mismo código que Kafka consumer)
    context = aggregate_context(event.user_id, event.data)

    # Publish next event
    from messaging import publish_event, ContextAggregatedEvent
    next_event = ContextAggregatedEvent(
        user_id=event.user_id,
        context_data=context
    )
    publish_event(next_event)  # ← También usa backend correcto


@shared_task(name="vectosvc.worker.tasks.process_context_aggregated")
def process_context_aggregated(event_dict: dict):
    """Fallback task for context.aggregated event"""
    # Similar implementation...
    pass


@shared_task(name="vectosvc.worker.tasks.ingest_vectors")
def ingest_vectors(event_dict: dict):
    """Fallback task for context.vectorized event"""
    # Similar implementation...
    pass
```

---

### 3. Configuración por Ambiente

#### Development (Local)

```bash
# .env.development
MESSAGING_BACKEND=kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092  # Docker local
```

#### Staging

```bash
# Railway staging environment
MESSAGING_BACKEND=kafka
KAFKA_BOOTSTRAP_SERVERS=pkc-staging.confluent.cloud:9092
```

#### Production

```bash
# Railway production environment
MESSAGING_BACKEND=kafka  # o "celery" si rollback necesario
KAFKA_BOOTSTRAP_SERVERS=pkc-prod.confluent.cloud:9092
```

---

## 📊 Monitoring para Detectar Problemas

### Alertas en Confluent Cloud

```yaml
# Configurar en Confluent Cloud → Alerts

Alert 1: Consumer Lag
  Condition: lag > 1000 mensajes
  Action: Email + Slack notification

Alert 2: Throughput Anómalo
  Condition: msgs/sec > 500 (inusual para tu escala)
  Action: Investigar producer en loop

Alert 3: Error Rate
  Condition: error_rate > 5%
  Action: Considerar rollback a Celery
```

### Metrics Dashboard

```python
# services/api/monitoring/metrics.py
from prometheus_client import Counter, Gauge

# Metrics
events_published = Counter(
    'aura360_events_published_total',
    'Total events published',
    ['backend', 'event_type']
)

messaging_backend = Gauge(
    'aura360_messaging_backend',
    'Current messaging backend (1=kafka, 2=celery, 0=disabled)'
)

# Update on startup
backend = os.getenv("MESSAGING_BACKEND", "kafka")
if backend == "kafka":
    messaging_backend.set(1)
elif backend == "celery":
    messaging_backend.set(2)
else:
    messaging_backend.set(0)
```

**Visualizar en Grafana**:
```
Panel 1: Messaging Backend Status
  - Gauge: kafka/celery/disabled

Panel 2: Events Published by Backend
  - Line chart: events_published_total{backend="kafka"}
  - Line chart: events_published_total{backend="celery"}

Panel 3: Consumer Lag (Kafka only)
  - Importado desde Confluent Cloud Metrics API
```

---

## 🧪 Testing de Rollback

### Test 1: Switch Manual (Pre-Production)

```bash
# 1. Deploy con Kafka
railway up --service api
railway variables set MESSAGING_BACKEND=kafka

# 2. Generar tráfico de prueba
curl -X POST https://api.railway.app/holistic/mood-entries/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"mood_score": 7, "tags": ["test"]}'

# 3. Verificar en Kafka UI: http://localhost:8090
# → Debería ver evento en aura360.user.events

# 4. Switch a Celery
railway variables set MESSAGING_BACKEND=celery
railway service restart api

# 5. Generar tráfico de prueba
curl -X POST https://api.railway.app/holistic/mood-entries/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"mood_score": 8, "tags": ["test2"]}'

# 6. Verificar en Flower (Celery UI): http://localhost:5555
# → Debería ver task process_mood_created ejecutado

# 7. Validar: datos llegaron a Qdrant en ambos casos
```

### Test 2: Chaos Engineering (Opcional)

```bash
# Simular falla de Confluent Cloud

# 1. Bloquear tráfico a Confluent
iptables -A OUTPUT -d pkc-xxxxx.confluent.cloud -j DROP

# 2. Aplicación debería detectar falla y usar Celery
# (requiere implement retry logic con fallback automático)

# 3. Restaurar
iptables -D OUTPUT -d pkc-xxxxx.confluent.cloud -j DROP
```

---

## 📋 Runbook: Rollback Paso a Paso

### Situación: Necesitas hacer rollback AHORA

**Tiempo estimado**: 5 minutos

```bash
# PASO 1: Cambiar variable de entorno (30 segundos)
railway variables set MESSAGING_BACKEND=celery

# PASO 2: Verificar que Celery workers están corriendo (30 segundos)
railway logs vectordb-worker --tail=50
# Esperado: "celery@worker ready"

# PASO 3: Restart servicios (2 minutos)
railway service restart api
railway service restart vectordb-api
railway service restart agents

# PASO 4: Verificar health checks (1 minuto)
curl https://api.railway.app/health
# Esperado: {"status": "ok", "messaging_backend": "celery"}

# PASO 5: Generar evento de prueba (1 minuto)
curl -X POST https://api.railway.app/holistic/mood-entries/ \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"mood_score": 7}'

# PASO 6: Verificar procesamiento (30 segundos)
railway logs vectordb-worker --tail=20
# Esperado: "Task process_mood_created succeeded"

# ✅ ROLLBACK COMPLETO
```

---

## 🔄 Recovery: Volver a Kafka después de Rollback

```bash
# PASO 1: Verificar que Confluent Cloud está disponible
curl -I https://pkc-xxxxx.confluent.cloud:9092
# Esperado: timeout o connection refused (normal, no es HTTP)

# Usar Confluent Cloud UI para verificar cluster health

# PASO 2: Cambiar variable (30 segundos)
railway variables set MESSAGING_BACKEND=kafka

# PASO 3: Restart servicios (2 minutos)
railway service restart api
railway service restart vectordb-api
railway service restart vectordb-consumer
railway service restart agents

# PASO 4: Verificar consumer lag inicial (1 minuto)
# Usar Claude Desktop con MCP:
# "Claude, ¿cuál es el consumer lag de todos los grupos?"

# O usar Confluent Cloud UI → Consumers

# PASO 5: Monitorear durante 30 minutos
# → Lag debería decrecer
# → No errores en logs
# → Throughput normal

# ✅ RECOVERY COMPLETO
```

---

## 💾 Data Recovery: Eventos Perdidos durante Rollback

### Problema

Durante rollback Kafka → Celery, eventos en Kafka quedan sin procesar.

### Solución: Replay Manual

```bash
# Opción A: Usar Kafka consumer CLI para replay
kafka-console-consumer \
  --bootstrap-server pkc-xxxxx.confluent.cloud:9092 \
  --topic aura360.user.events \
  --from-beginning \
  --max-messages 1000 \
  --consumer.config client.properties \
  > events_backup.jsonl

# Procesar manualmente o re-ingestar

# Opción B: Temporal consumer para replay
# Crear script: services/vectordb/scripts/replay_kafka_events.py
python scripts/replay_kafka_events.py \
  --topic aura360.user.events \
  --from-offset 1234 \
  --to-offset 5678
```

---

## 📚 Checklist de Preparación

Antes de ir a producción con Kafka:

- [ ] Celery tasks de fallback implementados
- [ ] `backend.py` agregado al módulo shared
- [ ] Views usan `publish_event()` en lugar de `EventPublisher` directo
- [ ] Tests de rollback ejecutados en staging
- [ ] Runbook impreso y disponible
- [ ] Alertas configuradas en Confluent Cloud
- [ ] Monitoring dashboard con `messaging_backend` gauge
- [ ] Documentación actualizada con proceso de rollback
- [ ] On-call engineer conoce el runbook
- [ ] Feature flag `MESSAGING_BACKEND` documentado en DEPLOYMENT.md

---

## 🎯 Decisión: Cuándo Usar Cada Modo

| Escenario | Backend Recomendado | Razón |
|-----------|---------------------|-------|
| Producción normal | `kafka` | Mejor performance, decoupling |
| Confluent Cloud down | `celery` | Fallback funcional |
| Debugging consumer bug | `disabled` (ese consumer) | Aislar problema |
| Testing local | `kafka` (Docker) | Simular producción |
| Año gratis terminó, sin presupuesto | `celery` | Evitar costos |
| Load testing | `kafka` | Evaluar límites reales |

---

## 📞 Contactos de Emergencia

**Confluent Cloud Issues**:
- Support Portal: https://support.confluent.io
- Status Page: https://status.confluent.io
- Emergency: verificar en cuenta Confluent Cloud

**Railway Issues**:
- Discord: https://discord.gg/railway
- Status: https://railway.app/status

**Internal Escalation**:
- DevOps Lead: @devops-lead (Slack)
- Backend Lead: @backend-lead (Slack)
- On-call: PagerDuty escalation

---

**Última actualización**: 2025-01-07
**Versión**: 1.0
**Owner**: DevOps Team
