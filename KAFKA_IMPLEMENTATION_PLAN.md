# AURA360 - Plan de Implementación: Event-Driven Architecture con Confluent

**Fecha**: 2025-01-07
**Timeline**: 1-2 semanas
**Complejidad**: Full Event-Driven
**Equipo**: Backend Dev (Python/Django), DevOps, Frontend/Mobile Dev
**Experiencia con Kafka**: Ninguna

---

## 📋 Executive Summary

AURA360 migrará de arquitectura basada en HTTP síncrono + Celery a **Event-Driven Architecture** usando **Apache Kafka (Confluent Cloud)**. Esto mejorará:

- ✅ **Decoupling**: Servicios independientes sin conocimiento mutuo
- ✅ **Resilencia**: Si un servicio cae, eventos se retienen y procesan después
- ✅ **Escalabilidad**: Fácil agregar consumers para procesar más carga
- ✅ **Extensibilidad**: Nuevas features = nuevos consumers, sin tocar código existente

**Beneficio del perk**: 1 año gratis de Confluent Cloud (valor ~$13,200 USD).

---

## 🏗️ Arquitectura Propuesta

### Antes (HTTP Síncrono)

```
Mobile App
    ↓ HTTP POST
Django API → (espera) → Agents Service
    ↓ HTTP POST
Django API → (espera) → Vectordb Service
    ↓
Celery Task → Redis → Worker → Qdrant
```

**Problemas**:
- Tight coupling (Django conoce a todos los servicios)
- Si Vectordb cae, Django devuelve error al usuario
- Difícil agregar nuevos consumers (ej: analytics, notifications)

### Después (Event-Driven)

```
Mobile App
    ↓ HTTP POST
Django API
    ↓ publish event
┌─────────────────────────────────────────────────────────────┐
│                    KAFKA (Confluent Cloud)                  │
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
    │Context  │         │  Guardian │       │ Vectordb  │
    │Aggreg.  │         │  Consumer │       │ Consumer  │
    └─────────┘         └───────────┘       └───────────┘
```

**Ventajas**:
- Django solo publica evento y retorna 201 inmediatamente
- Consumers procesan en paralelo
- Agregar analytics/notifications = agregar consumer nuevo
- Si Vectordb cae, Kafka retiene eventos para replay

---

## 📅 Timeline Detallado (14 días)

| Días | Fase | Responsable | Entregables |
|------|------|-------------|-------------|
| 1-3 | Setup & Fundamentos | DevOps + Backend | docker-compose.dev.yml, módulo shared/messaging, POCs |
| 4-6 | Django API Event Publishing | Backend Django | Views publicando eventos en lugar de HTTP calls |
| 4-7 | Vectordb Event Consumption | Backend FastAPI | Consumers procesando context aggregation/vectorization |
| 7-9 | Agents Guardian Communication | Backend Agents | Request-reply pattern para Guardian advice |
| 8-10 | Mobile/Frontend Integration | Frontend/Mobile | WebSocket streaming de respuestas |
| 10-14 | DevOps Deployment | DevOps | Deploy a Railway, monitoring, runbooks |
| 12-14 | Testing & Validation | Todo el equipo | E2E tests, load testing, bug fixing |

---

## 👥 Roles y Responsabilidades

### **DevOps Lead** 🔧

**Días 1-3:**
- [ ] Activar Confluent Cloud (1 año gratis)
- [ ] Crear cluster en us-east-1 (Basic tier)
- [ ] Crear 6 topics con retention 7 días
- [ ] Obtener API Keys + Bootstrap URL
- [ ] **Setup Confluent MCP Server** (15 min):
  - [ ] Instalar Node.js 22
  - [ ] Crear `.env` con credenciales Confluent
  - [ ] Configurar Claude Desktop con MCP
  - [ ] Verificar: "Claude, lista todos los topics"
- [ ] Crear docker-compose.dev.yml con Kafka local
- [ ] Configurar Kafka UI para debugging

**Días 10-14:**
- [ ] Crear Dockerfiles para nuevos consumers
- [ ] Setup Confluent Cloud para producción (ACLs, monitoring)
- [ ] Actualizar DEPLOYMENT.md
- [ ] Configurar secrets en Railway
- [ ] Deploy staging → smoke tests → production
- [ ] Setup alerting (Confluent + Railway)

**Entregables:**
1. Confluent Cloud configurado
2. docker-compose.dev.yml funcional
3. Secrets en Railway
4. DEPLOYMENT.md actualizado
5. Monitoring dashboard

---

### **Backend Developer (Django)** 🐍

**Días 1-3:**
- [ ] Estudiar Confluent fundamentals (2h curso gratis)
- [ ] Crear módulo `services/shared/messaging/`
  - `kafka_producer.py`
  - `kafka_consumer.py`
  - `events.py` (schemas)
  - `config.py`
- [ ] POC: "Hello Kafka" (publisher → consumer local)
- [ ] Tests unitarios para producer/consumer

**Días 4-6:**
- [ ] Refactorizar `services/api/holistic/context_aggregator.py`
- [ ] Modificar views para publicar eventos:
  - `POST /api/holistic/mood-entries/` → publish `user.mood.created`
  - `POST /api/holistic/activities/` → publish `user.activity.created`
  - `POST /api/holistic/ikigai/` → publish `user.ikigai.updated`
- [ ] Implementar event publisher en `holistic/kafka_publisher.py`
- [ ] Agregar idempotency keys
- [ ] Tests de integración

**Entregables:**
1. Módulo shared/messaging reutilizable
2. Django API publicando eventos
3. Tests (80%+ coverage)
4. Documentación de schemas

---

### **Backend Developer (Vectordb FastAPI)** 🚀

**Días 4-7:**
- [ ] Crear `services/vectordb/vectosvc/kafka/`
  - `consumer.py`
  - `handlers.py`
- [ ] Implementar `ContextAggregationHandler`
  - Consume: `user.mood.created`
  - Publica: `context.aggregated`
- [ ] Implementar `ContextVectorizationHandler`
  - Consume: `context.aggregated`
  - Publica: `context.vectorized`
- [ ] Implementar `VectordbIngestHandler`
  - Consume: `context.vectorized`
  - Inserta en Qdrant
- [ ] Crear Dockerfile.consumer
- [ ] Migrar Celery tasks actuales a Kafka (mantener Celery solo para batch PDF processing)
- [ ] Tests end-to-end: Mood entry → Qdrant

**Entregables:**
1. Consumers funcionando localmente
2. Pipeline completo: User event → Context → Vectors → Qdrant
3. Tests E2E
4. Dockerfile.consumer

---

### **Backend Developer (Agents Service)** 🧠

**Días 7-9:**
- [ ] Crear `services/agents/kafka/consumer.py`
- [ ] Implementar `GuardianRequestHandler`
  - Consume: `guardian.requests`
  - Ejecuta Guardian agent
  - Publica: `guardian.responses`
- [ ] Refactorizar `services/holistic.py` para usar Kafka
  - Request-reply pattern con correlation ID
- [ ] Implementar timeout handling (30s)
- [ ] (Opcional) Implementar streaming responses:
  - Guardian emite chunks a `guardian.response.chunks`
  - Django consume y pushea via WebSocket
- [ ] Tests: Request advice → response en Kafka

**Entregables:**
1. Guardian consumer funcionando
2. Request-reply pattern implementado
3. (Opcional) Streaming responses
4. Tests de integración

---

### **Frontend/Mobile Developer** 📱

**Días 8-10:**
- [ ] Actualizar Flutter app para WebSocket connection a Django
- [ ] Implementar UI que muestre respuestas progresivas de Guardians
- [ ] Agregar indicadores de estado (procesando, vectorizando, etc.)
- [ ] (Si aplica) Actualizar Angular app
- [ ] Tests E2E desde UI: Create mood → ver proceso → recibir advice
- [ ] Polish UX: loading states, error handling
- [ ] Testing en dispositivos reales

**Entregables:**
1. Flutter app con WebSocket streaming
2. UI con estados de procesamiento
3. Error handling robusto
4. Tests E2E desde UI

---

## 📊 Métricas de Éxito

### KPIs Técnicos

| Métrica | Target | Herramienta |
|---------|--------|-------------|
| Latencia end-to-end | <5 segundos | Confluent Cloud Metrics |
| Consumer lag | <100ms promedio | Confluent Cloud Dashboard |
| Event delivery rate | 100% (0 pérdidas) | Kafka delivery reports |
| Test coverage | >80% | pytest --cov |
| Uptime | >99.5% | Railway + Confluent monitoring |

### KPIs de Negocio

- ✅ 0 llamadas HTTP síncronas entre servicios
- ✅ Capacidad de agregar features sin modificar código existente
- ✅ Rollback plan funcional en caso de problemas
- ✅ Documentación completa para onboarding

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Equipo sin experiencia en Kafka (ALTO)

**Impacto**: Errores de implementación, timeline alargado

**Mitigación**:
- ✅ Día 1: Todo el equipo completa Confluent Academy (4h curso gratis)
- ✅ DevOps hace POC primero, luego enseña al equipo en daily standups
- ✅ Usar abstracciones del módulo shared/messaging (simplifica API)
- ✅ Code reviews exhaustivos por alguien con experiencia en event-driven

### Riesgo 2: Bugs en producción por complejidad event-driven (MEDIO)

**Impacto**: Downtime, pérdida de eventos, UX degradada

**Mitigación**:
- ✅ Deploy gradual: 1% → 10% → 50% → 100% tráfico
- ✅ Feature flag para rollback a Celery si algo falla
- ✅ Monitoring desde día 1 (Confluent + Railway alerts)
- ✅ Runbooks para troubleshooting común

### Riesgo 3: Consumer lag en producción (MEDIO)

**Impacto**: Latencia alta percibida por usuarios

**Mitigación**:
- ✅ Load testing antes de producción (simular 100 usuarios concurrentes)
- ✅ Auto-scaling de consumers en Railway (configurar desde inicio)
- ✅ Alertas en Confluent Cloud si lag > 1000 mensajes
- ✅ Optimization checklist: partitions, consumer concurrency, batch sizes

### Riesgo 4: Timeline agresivo (1-2 semanas) (ALTO)

**Impacto**: No se completa implementación, deployment incompleto

**Mitigación**:
- ✅ Checkpoint GO/NO-GO en día 7:
  - Si POC funciona → continuar
  - Si no funciona → pivotear a implementación Balanced (mantener más Celery)
- ✅ Priorizar features: CDC + User Events (MUST) > Guardian Streaming (NICE)
- ✅ Daily standups de 15 min para identificar blockers temprano
- ✅ Tener a alguien disponible full-time (no part-time entre proyectos)

---

## 🚦 Checkpoint GO/NO-GO (Día 7)

### Criterios GO

- [ ] POC funciona localmente (publisher → consumer)
- [ ] Equipo entiende conceptos básicos (topics, partitions, consumer groups)
- [ ] Django publica eventos correctamente
- [ ] Vectordb consume eventos correctamente
- [ ] 0 blockers críticos identificados
- [ ] Timeline tracking on schedule

### Criterios NO-GO

Si falla alguno de los anteriores:

**Plan B**: Pivotear a implementación **Balanced**:
- Mantener HTTP calls para Guardian requests (crítico para UX)
- Solo migrar context aggregation a Kafka
- Reducir scope para cumplir timeline

---

## 📚 Recursos de Aprendizaje

### Día 1 - TODO EL EQUIPO (4 horas)

**Obligatorio**:
1. [Confluent Fundamentals](https://developer.confluent.io/courses/apache-kafka/events/) (2h)
2. [Event-Driven Architecture 101](https://www.confluent.io/learn/event-driven-architecture/) (1h)
3. Leer `services/shared/README.md` (30 min)
4. Ejecutar QUICKSTART_KAFKA.md (30 min)

**Opcional**:
- [Kafka Patterns](https://developer.confluent.io/patterns/) (1h)
- [Request-Reply Pattern](https://www.confluent.io/blog/request-reply-pattern-apache-kafka/) (30 min)

### Referencias Rápidas

- **Módulo shared**: `services/shared/README.md`
- **Quickstart**: `QUICKSTART_KAFKA.md`
- **Deployment**: `DEPLOYMENT.md` (sección Confluent)
- **Event Schemas**: `services/shared/messaging/events.py`
- **MCP Setup**: `MCP_CONFLUENT_SETUP.md` ⭐ NUEVO
- **Confluent Docs**: https://docs.confluent.io/kafka-clients/python/current/
- **Kafka UI Local**: http://localhost:8090
- **Claude Desktop con MCP**: Gestión conversacional de Kafka

---

## 🔄 Workflow Diario Recomendado

### Daily Standup (15 min, 9:00 AM)

**Agenda**:
1. Cada rol reporta: ¿Qué hice ayer? ¿Qué haré hoy? ¿Algún blocker?
2. DevOps Lead actualiza timeline tracker (¿vamos on track?)
3. Resolver blockers críticos o escalar

### Code Review Policy

**Obligatorio para**:
- Todos los cambios en `services/shared/messaging/`
- Implementaciones de consumers
- Cambios en event schemas

**Revisor**: Alguien con experiencia en event-driven o DevOps Lead

### Testing antes de Merge

**Checklist**:
- [ ] Unit tests pasan (`pytest`)
- [ ] Integration test manual (publisher → consumer local)
- [ ] Verificado en Kafka UI (mensaje visible en topic)
- [ ] Code review aprobado
- [ ] No rompe build de otros servicios

---

## 📦 Entregables Finales

### Código

1. ✅ `services/shared/messaging/` - Módulo compartido
2. ✅ `docker-compose.dev.yml` - Infra local con Kafka
3. ✅ Django API publicando eventos
4. ✅ Vectordb consumers procesando eventos
5. ✅ Agents consumers para Guardian requests
6. ✅ (Opcional) Flutter WebSocket streaming

### Documentación

1. ✅ `KAFKA_IMPLEMENTATION_PLAN.md` (este documento)
2. ✅ `QUICKSTART_KAFKA.md` - Guía de inicio rápido
3. ✅ `services/shared/README.md` - Docs del módulo messaging
4. ✅ `DEPLOYMENT.md` actualizado con sección Confluent
5. ✅ Runbooks de troubleshooting

### Infraestructura

1. ✅ Confluent Cloud configurado (producción)
2. ✅ Kafka local en Docker (desarrollo)
3. ✅ Secrets configurados en Railway
4. ✅ Monitoring dashboard (Confluent + Railway)
5. ✅ Alertas configuradas (consumer lag, errors)

---

## 🎯 Siguiente Acción Inmediata

**Para empezar AHORA**:

1. **DevOps**: Activar cuenta Confluent Cloud (5 min)
   ```
   https://confluent.cloud → Sign Up → Activar perk 1 año gratis
   ```

2. **Backend Devs**: Levantar Kafka local (5 min)
   ```bash
   cd /path/to/AURA360
   docker-compose -f docker-compose.dev.yml up -d
   open http://localhost:8090  # Verificar Kafka UI
   ```

3. **TODO EL EQUIPO**: Completar learning resources (4h)
   ```
   Confluent Fundamentals → Event-Driven Architecture 101 → QUICKSTART_KAFKA.md
   ```

4. **Daily Standups**: Schedule diario de 15 min (9:00 AM)

---

## 💰 Costos Post Año-Gratis

### Opción 1: Self-Host Kafka en Railway
- **Costo**: ~$150-300/mes
- **Pros**: Control total, más barato que Confluent paid
- **Contras**: Overhead operacional, pierdes features managed

### Opción 2: Confluent Cloud Paid
- **Costo**: ~$1,100/mes (Standard tier)
- **Pros**: Fully managed, auto-scaling, soporte 24/7
- **Contras**: Costoso si revenue < $10K/mes

### Opción 3: Hybrid (Recomendado)
- **Costo**: ~$300/mes
- **Stack**: Self-hosted Kafka para eventos críticos + Celery para batch jobs
- **Pros**: Balance costo/features
- **Contras**: Complejidad de mantener ambos

**Decisión en Mes 10**: Evaluar revenue y escala antes de que expire el año gratis.

---

## ✅ Checklist Final Pre-Deployment

Antes de deploy a producción, verificar:

- [ ] Todos los tests E2E pasan (móvil → Django → Kafka → Vectordb → Qdrant)
- [ ] Load test con 100 usuarios simulados exitoso (consumer lag <500ms)
- [ ] Confluent Cloud configurado con topics + ACLs correctos
- [ ] Secrets de Confluent en Railway (API Key, Bootstrap URL)
- [ ] Monitoring dashboard funcional (Confluent + Railway)
- [ ] Alertas configuradas (consumer lag >1000, error rate >1%)
- [ ] Runbooks documentados (troubleshooting común)
- [ ] Rollback plan probado (feature flag para volver a Celery)
- [ ] Code review completo (por alguien con experiencia event-driven)
- [ ] Documentación actualizada (DEPLOYMENT.md, README.md, CLAUDE.md)
- [ ] Onboarding docs para futuros devs
- [ ] Backup de configuración (topics, partitions, retention policies)

---

**🚀 Listo para empezar! Siguiente paso: Ver QUICKSTART_KAFKA.md para hands-on.**

---

**Última actualización**: 2025-01-07
**Versión**: 1.0
**Contacto**: freakscode (Architect/Tech Lead)
