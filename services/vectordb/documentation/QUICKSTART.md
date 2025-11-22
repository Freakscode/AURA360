# 🚀 Quick Start - Vectorial DB (AURA365)

## ✅ Estado Actual

**Fase 1 COMPLETADA y VERIFICADA** - Sistema 100% funcional en Docker

## 🏃 Comandos Básicos

### **Iniciar el Sistema**

```bash
cd "/Users/freakscode/Proyectos 2025/AURA365/vectorial_db"

# Levantar todos los servicios
docker compose up -d

# Ver estado
docker compose ps

# Ver logs en tiempo real
docker compose logs -f api worker
```

### **Detener el Sistema**

```bash
# Detener sin eliminar datos
docker compose stop

# Detener y eliminar todo (incluye datos)
docker compose down -v
```

## ⚙️ Variables de entorno clave

Define un archivo `.env` (usado por `docker compose`) con las credenciales y timeouts necesarios para el pipeline de planes nutricionales:

```ini
# Supabase Storage para descargar PDFs privados
SUPABASE_API_URL=http://127.0.0.1:54321
SUPABASE_SERVICE_ROLE_KEY=change-me

# DeepSeek 7B (o el modelo que uses)
DEEPSEEK_API_URL=http://localhost:9000/v1/chat/completions
DEEPSEEK_API_KEY=local-deepseek-token
DEEPSEEK_TIMEOUT=60

# Ajustes del pipeline
NUTRITION_PLAN_DOWNLOAD_TIMEOUT=30
NUTRITION_PLAN_CALLBACK_TIMEOUT=15
NUTRITION_PLAN_PROMPT_MAX_CHARS=12000
NUTRITION_PLAN_LLM_MODEL=deepseek-7b
NUTRITION_PLAN_LLM_TEMPERATURE=0.15
NUTRITION_PLAN_LLM_MAX_OUTPUT_TOKENS=1400
NUTRITION_PLAN_LLM_RESPONSE_EXCERPT=1200
NUTRITION_PLAN_TEXT_EXCERPT=1500

# Callback al backend (coincide con NUTRITION_PLAN_CALLBACK_URL/TOKEN del backend)
NUTRITION_PLAN_CALLBACK_URL=http://localhost:8000/dashboard/internal/nutrition-plans/ingest-callback/
NUTRITION_PLAN_CALLBACK_TOKEN=backend-callback-secret
```

> Si ejecutas el worker fuera de Docker, exporta las mismas variables en tu shell antes de lanzar `uv run celery -A vectosvc.worker.tasks worker`.

## 📝 Ejemplos de Uso

### **1. Health Check**

```bash
curl http://localhost:8000/readyz
# → {"status": "ok"}
```

### **2. Ingestar un Documento**

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "mi-documento-001",
    "text": "Tu texto aquí...",
    "metadata": {
      "topics": ["sleep_health", "cognitive_function"],
      "year": 2024,
      "journal": "Journal Name",
      "source": "manual"
    }
  }'

# Respuesta:
# {"job_id": "abc-123...", "status": "queued"}
```

### **3. Consultar Estado de un Job**

```bash
curl http://localhost:8000/jobs/abc-123...
# → {"status": "completed", "processed_chunks": 5, ...}
```

### **4. Buscar Documentos**

```bash
# Búsqueda simple
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "melatonina y sueño",
    "limit": 5
  }'

# Búsqueda con filtros
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "efectos del ejercicio",
    "limit": 10,
    "filter": {
      "must": {
        "topics": ["exercise_physiology"],
        "year": 2024
      }
    }
  }'
```

### **5. Ingesta Batch (Múltiples Documentos)**

```bash
curl -X POST http://localhost:8000/ingest/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "doc_id": "doc-001",
      "text": "Texto del documento 1...",
      "metadata": {"topics": ["sleep_health"], "year": 2024}
    },
    {
      "doc_id": "doc-002",
      "text": "Texto del documento 2...",
      "metadata": {"topics": ["nutrition"], "year": 2024}
    }
  ]'

# Respuesta:
# {"job_ids": ["abc-123...", "def-456..."], "status": "queued"}
```

### **6. Ver Métricas del Sistema**

```bash
# Métricas completas
curl http://localhost:8000/metrics | jq

# Solo caché
curl http://localhost:8000/metrics | jq .cache

# Solo pipeline
curl http://localhost:8000/metrics | jq .pipeline

# Solo colección
curl http://localhost:8000/metrics | jq .collection
```

### **7. Monitorear DLQ (Fallos)**

```bash
# Ver estadísticas de fallos
curl http://localhost:8000/dlq/stats | jq

# Listar últimos 10 fallos
curl http://localhost:8000/dlq?limit=10 | jq

# Limpiar DLQ (después de analizar)
curl -X DELETE http://localhost:8000/dlq
```

## 📊 Monitoreo en Tiempo Real

### **Logs del Worker**

```bash
# Ver logs de ingesta
docker compose logs -f worker | grep -E "(Ingested|cache|chunks)"

# Ver todos los logs
docker compose logs -f worker
```

### **Logs de la API**

```bash
# Ver requests
docker compose logs -f api | grep "HTTP"

# Ver errores
docker compose logs -f api | grep "ERROR"
```

### **Métricas Continuas**

```bash
# Actualizar cada 5 segundos
watch -n 5 'curl -s http://localhost:8000/metrics | jq .collection'
```

## 🧪 Testing Rápido

### **Script de Prueba Completo**

```bash
#!/bin/bash

echo "🧪 Testing Vectorial DB..."

# 1. Health check
echo "✓ Health check..."
curl -s http://localhost:8000/readyz | jq

# 2. Ingestar documento
echo "✓ Ingestando documento..."
RESULT=$(curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test-'$(date +%s)'",
    "text": "Test de ingesta con timestamp",
    "metadata": {"topics": ["test"], "year": 2024}
  }')
JOB_ID=$(echo $RESULT | jq -r .job_id)
echo "Job ID: $JOB_ID"

# 3. Esperar y verificar
echo "✓ Esperando procesamiento..."
sleep 5
curl -s http://localhost:8000/jobs/$JOB_ID | jq

# 4. Buscar
echo "✓ Buscando..."
curl -s -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "limit": 3}' | jq '.hits | length'

# 5. Métricas
echo "✓ Métricas:"
curl -s http://localhost:8000/metrics | jq '{
  documents: .collection.total_documents,
  points: .collection.total_points,
  cache_hit_rate: .cache.hit_rate_percent
}'

echo "✅ Test completado!"
```

## 🔧 Comandos de Utilidad

### **Reiniciar Solo un Servicio**

```bash
# Reiniciar worker (útil después de cambios)
docker compose restart worker

# Reiniciar API
docker compose restart api
```

### **Ver Contenido de Redis**

```bash
# Conectarse a Redis
docker compose exec redis redis-cli

# Ver keys de caché de embeddings
KEYS emb:v1:*

# Ver estadísticas de DLQ
HGETALL dlq:stats

# Salir
EXIT
```

### **Ver Colecciones en Qdrant**

```bash
# Listar colecciones
curl http://localhost:6333/collections | jq

# Info de colección 'docs'
curl http://localhost:6333/collections/docs | jq
```

### **Backup de Qdrant**

```bash
# Crear snapshot
curl -X POST http://localhost:6333/collections/docs/snapshots

# Listar snapshots
curl http://localhost:6333/collections/docs/snapshots | jq

# Los snapshots están en: vectorial_db_qdrant_storage/snapshots/
```

## 📈 Performance Verificada

| Métrica | Valor |
|---------|-------|
| Cache Hit Mejora | **90%** (11.13s → 1.12s) |
| Búsqueda Latency | **< 100ms** |
| Ingesta Throughput | **~5 docs/min** (sin paralelo) |
| Vector Size | 384 dims (MiniLM) |
| Distance Metric | Cosine |

## 🎯 Topics Disponibles

Ver lista completa en `config/topics.yaml`. Principales:

- `sleep_health`, `circadian_rhythm`, `sleep_deprivation`
- `insomnia`, `hypersomnia`, `obstructive_sleep_apnea`
- `metabolism_disorders`, `obesity`, `type2_diabetes`
- `stress_response`, `inflammation`, `cardiovascular_health`
- `cognitive_function`, `mental_health`, `nutrition`
- Y más... (37 topics totales)

## 🐛 Troubleshooting

### **Contenedor no inicia**

```bash
# Ver logs detallados
docker compose logs <servicio>

# Rebuild forzado
docker compose build --no-cache <servicio>
docker compose up -d <servicio>
```

### **API retorna 500**

```bash
# Ver logs de API
docker compose logs api --tail=50

# Verificar que Qdrant y Redis están corriendo
docker compose ps
```

### **Worker no procesa jobs**

```bash
# Ver logs de worker
docker compose logs worker --tail=50

# Verificar conexión a Redis
docker compose exec worker redis-cli -h redis PING

# Reiniciar worker
docker compose restart worker
```

### **Caché no funciona**

```bash
# Verificar que Redis está corriendo
docker compose exec redis redis-cli PING

# Ver keys de caché
docker compose exec redis redis-cli KEYS "emb:v1:*"

# Ver configuración
curl http://localhost:8000/metrics | jq .cache
```

## 📚 Documentación Adicional

- **Plan completo**: `PlanDeImplementacion.md`
- **Fase 1 completada**: `FASE1_COMPLETED.md`
- **README general**: `README.md`

## 🚀 Próximos Pasos

Para Fase 1.5:
- [ ] Implementar boosts en búsqueda (abstract/conclusion)
- [ ] Configurar Grafana/Prometheus para métricas
- [ ] Agregar alertas automáticas

Para Fase 2:
- [ ] Caché de resultados de búsqueda
- [ ] Re-ranker cross-encoder
- [ ] Búsqueda híbrida (dense + sparse)

---

**¿Necesitas ayuda?** Revisa los logs:
```bash
docker compose logs -f
```

