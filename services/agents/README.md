# Agentes Holísticos con Google ADK y servicio vectorial

Este servicio orquesta un conjunto de agentes especializados (físico, mental y espiritual) mediante Google ADK. Para la recuperación de contexto se integra con el servicio vectorial `vectorial_db` (Qdrant + API FastAPI) ejecutado en local.

## Instalación

```bash
cd "/Users/freakscode/Proyectos 2025/AURA360/agents-service"
uv sync
```

## Variables de entorno clave

⚠️ **IMPORTANTE**: El servicio carga **automáticamente** las variables desde el archivo `.env` ubicado en la raíz del proyecto. **Ya NO es necesario usar `export` manual** en la terminal.

### Configuración Rápida

1. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```

2. Edita el archivo `.env` con tus valores.

3. Verifica la carga de variables:
   ```bash
   uv run python scripts/test_env_loading.py
   ```

### Variables Requeridas

Asegúrate de que tu archivo `.env` incluya, como mínimo:

```bash
# Servicio Vectorial / Qdrant
VECTOR_SERVICE_URL=http://localhost:6333
VECTOR_SERVICE_COLLECTION_NAME=docs  # REQUERIDO
VECTOR_SERVICE_TIMEOUT=30
VECTOR_SERVICE_VERIFY_SSL=false

# Embeddings
AGENT_DEFAULT_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
AGENT_SERVICE_EMBEDDING_BACKEND=fastembed  # o "gemini"
AGENT_SERVICE_EMBEDDING_NORMALIZE=true

# Google API (solo si usas backend=gemini)
GOOGLE_API_KEY=tu_api_key_aqui
```

### Variables Opcionales

- `AGENT_SERVICE_VECTOR_STORE_NAME` (default: `qdrant`)
- `AGENT_SERVICE_VECTOR_RETRIES` y `AGENT_SERVICE_VECTOR_BACKOFF`
- `AGENT_SERVICE_VECTOR_TOP_K`
- `AGENT_SERVICE_MODEL_VERSION`

### Documentación Completa

Consulta [**docs/environment_variables.md**](docs/environment_variables.md) para:
- ✓ Cómo funciona la carga automática
- ✓ Troubleshooting de problemas comunes
- ✓ Variables legacy vs. nuevas
- ✓ Integración con IDEs

Durante la inicialización, la aplicación utiliza [`infra/env.py`](infra/env.py) para cargar automáticamente los archivos `.env` disponibles (`.env`, `.env.local`). Las rutas se resuelven de forma absoluta, por lo que el archivo `.env` se carga correctamente sin importar desde qué directorio ejecutes el comando.

## Ejecutar `vectorial_db`

1. Ve a la carpeta del servicio vectorial:
   ```bash
   cd "/Users/freakscode/Proyectos 2025/AURA360/vectorial_db"
   ```
2. Levanta la infraestructura (Qdrant, Redis, GROBID, API, worker):
   ```bash
   docker compose up -d
   ```
3. Verifica que la API esté disponible en `http://localhost:8001/readyz`.

## Ejecución del servicio FastAPI

```bash
uv run uvicorn main:app --reload --port 8080
```

Endpoint principal:

```
POST /api/v1/holistic/advice
```

Payload esperado:

```json
{
  "trace_id": "uuid-o-similar",
  "category": "mind|body|soul|holistic",
  "user_profile": {...},
  "preferences": {...},
  "context": "Texto opcional o estructura"
}
```

Respuesta (éxito):

```json
{
  "status": "success",
  "data": {
    "summary": "...",
    "recommendations": [...],
    "agent_runs": [
      {
        "agent_name": "...",
        "status": "completed",
        "latency_ms": 123,
        "input_context": {...},
        "output_payload": {...},
        "vector_queries": [...]
      }
    ]
  },
  "error": null,
  "meta": {
    "trace_id": "...",
    "model_version": "1.0.0",
    "timestamp": "ISO8601"
  }
}
```

En caso de error se retorna `"status": "error"` con campos `error.type` y `error.message`.

## Pruebas

```bash
uv run pytest
```

Las pruebas unitarias principales se encuentran en [`tests/test_holistic_advice_endpoint.py`](tests/test_holistic_advice_endpoint.py) y cubren:
- Flujo de éxito con mocks del servicio
- Categoría no soportada (422)
- Fallos de vector store (502)

## Ingesta de documentos

**IMPORTANTE**: La ingesta de documentos se realiza directamente en el servicio `vectorial_db`, NO en este servicio de agentes.

Para ingestar documentos al sistema vectorial:

```bash
cd "/Users/freakscode/Proyectos 2025/AURA360/vectorial_db"

# Usando scripts del servicio vectorial
uv run python scripts/ingest_batch.py ./data/papers.jsonl

# O usando el API directamente
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{"doc_id": "doc1", "text": "contenido...", "metadata": {...}}'
```

Consulta la [documentación de vectorial_db](../vectorial_db/documentation/QUICKSTART.md) para más opciones de ingesta.

## Scripts de validación

- Smoke test del agente de recuperación:
  ```bash
  uv run python scripts/smoke_retrieval.py
  ```
  > Valida que el backend de embeddings coincida en dimensionalidad con la colección de Qdrant.

### Variable `SMOKE_SKIP_DIM_CHECK`

Para saltar temporalmente la verificación dimensional:

```bash
SMOKE_SKIP_DIM_CHECK=true uv run python scripts/smoke_retrieval.py
```

Úsala solo en migraciones controladas.

## Recursos adicionales

- [`vectorial_db` documentation](../vectorial_db/documentation/INDEX.md)
- [Documentación Qdrant](https://qdrant.tech/documentation/)
- [Google ADK](https://ai.google.dev/gemini-api/docs/adk/overview)
