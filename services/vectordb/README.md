# Vectorial DB - AURA365

Servicio de base de datos vectorial (Qdrant) para búsqueda semántica sobre documentos biomédicos.

## 🚀 Quick Start

```bash
# Iniciar el sistema
docker compose up -d

# Ver estado
docker compose ps

# Detener
docker compose stop
```

## 📚 Documentación

Toda la documentación del proyecto está organizada en la carpeta [`documentation/`](./documentation/):

- **[📑 INDEX.md](./documentation/INDEX.md)** - Índice completo de documentación (empieza aquí)
- **[🚀 QUICKSTART.md](./documentation/QUICKSTART.md)** - Guía rápida con comandos y ejemplos
- **[📋 PlanDeImplementacion.md](./documentation/PlanDeImplementacion.md)** - Plan completo del proyecto
- **[✅ FASE1_COMPLETED.md](./documentation/FASE1_COMPLETED.md)** - Documentación técnica Fase 1
- **[📊 RESUMEN_FASE1.txt](./documentation/RESUMEN_FASE1.txt)** - Resumen ejecutivo

## 🎯 Estado Actual

✅ **Fase 1 COMPLETADA** - Sistema 100% funcional

### Características Implementadas:
- ✅ Caché de embeddings en Redis (90% más rápido)
- ✅ Métricas detalladas del pipeline
- ✅ Dead Letter Queue (DLQ) para auditoría
- ✅ Ingesta con GROBID + fallback PyMuPDF
- ✅ Búsqueda semántica con filtros
- ✅ Clasificación de 37 topics biomédicos
- ✅ Soporte GCS, HTTP, filesystem

## 🔧 Tecnologías

- **Python 3.11** - Lenguaje base
- **FastAPI** - API REST
- **Celery + Redis** - Worker asíncrono y caché
- **Qdrant** - Base de datos vectorial
- **GROBID** - Extracción de metadatos de PDFs
- **FastEmbed** - Generación de embeddings

## 📊 Performance Verificada

| Métrica | Valor |
|---------|-------|
| Cache Hit Mejora | **90%** (11.13s → 1.12s) |
| Búsqueda Latency | **< 100ms** |
| Vector Size | 384 dims (MiniLM) |
| Distance Metric | Cosine |

## 🛠️ Comandos Útiles

```bash
# Ver logs en tiempo real
docker compose logs -f api worker

# Ver métricas del sistema
curl http://localhost:8000/metrics | jq

# Ingestar un documento
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "test", "text": "...", "metadata": {...}}'

# Buscar documentos
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "...", "limit": 5}'
```

## 📖 Más Información

Para detalles completos de uso, ejemplos y troubleshooting, consulta el **[QUICKSTART.md](./documentation/QUICKSTART.md)**.

---

**Proyecto**: AURA365 - Servicio de Base de Datos Vectorial  
**Estado**: ✅ Fase 1 Completa - Producción Ready  
**Fecha**: Octubre 2025

