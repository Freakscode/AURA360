# Variables de Entorno - Agents Service

## Resumen

El servicio de agentes carga automáticamente las variables de entorno desde el archivo `.env` ubicado en la raíz del proyecto. **No es necesario usar `export` manual** en la terminal.

## Cómo Funciona

### 1. Carga Automática

El sistema carga variables de entorno en dos puntos:

1. **Durante imports** (`agents_service/__init__.py`):
   - Se ejecuta `load_environment()` ANTES de importar cualquier módulo
   - Garantiza que las variables estén disponibles para código que se ejecuta al nivel del módulo

2. **Al iniciar el servidor** (`main.py`):
   - Se ejecuta `load_environment()` nuevamente (se salta si ya se cargó)
   - Muestra logs informativos sobre qué archivos se cargaron

### 2. Resolución de Rutas

El sistema usa **rutas absolutas** al archivo `.env`:

- `infra/settings.py`: Usa `Path(__file__).resolve().parent.parent / ".env"`
- `infra/env.py`: Usa la misma resolución de rutas

Esto significa que el archivo `.env` se carga correctamente **sin importar desde qué directorio ejecutes el comando**.

### 3. Archivos Buscados

El sistema busca los siguientes archivos (en orden):

1. `.env` (principal)
2. `.env.local` (opcional, para configuración local que no se commitea)

## Variables Requeridas

### Variables del Servicio Vectorial

```bash
# URL del servicio Qdrant
VECTOR_SERVICE_URL=http://localhost:6333

# Nombre de la colección (REQUERIDO)
VECTOR_SERVICE_COLLECTION_NAME=docs

# API Key (opcional para desarrollo local)
VECTOR_SERVICE_API_KEY=

# Timeout en segundos
VECTOR_SERVICE_TIMEOUT=30

# Verificar SSL (false para desarrollo local)
VECTOR_SERVICE_VERIFY_SSL=false
```

### Variables de Embeddings

```bash
# Modelo de embeddings
AGENT_DEFAULT_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# Backend: "fastembed" (local) o "gemini" (API)
AGENT_SERVICE_EMBEDDING_BACKEND=fastembed

# Normalizar embeddings
AGENT_SERVICE_EMBEDDING_NORMALIZE=true

# API Key para Google (solo si usas backend=gemini)
GOOGLE_API_KEY=tu_api_key_aqui
```

### Variables de Configuración del Servicio

```bash
# Versión del modelo
AGENT_SERVICE_MODEL_VERSION=1.0.0

# Horizonte de recomendaciones en días
AGENT_SERVICE_RECOMMENDATION_HORIZON_DAYS=21

# URL de Qdrant (alternativa)
AGENT_SERVICE_QDRANT_URL=http://localhost:6333

# Colección vectorial (alternativa)
AGENT_SERVICE_VECTOR_COLLECTION=docs
```

## Verificar Carga de Variables

### Script de Prueba

Ejecuta el script de prueba para verificar que las variables se cargan correctamente:

```bash
uv run python scripts/test_env_loading.py
```

Este script verifica:
- ✓ Que el archivo `.env` existe
- ✓ Que las variables críticas están definidas
- ✓ Que `ServiceSettings` puede acceder a las variables
- ✓ Muestra los valores cargados (ocultando API keys)

### Salida Esperada

```
================================================================================
TEST 1: Cargando variables con infra.env.load_environment()
================================================================================
✓ Cargando variables desde: /path/to/agents-service/.env
Variables cargadas desde 1 archivo(s)

================================================================================
TEST 2: Verificando variables de entorno críticas
================================================================================
✓ GOOGLE_API_KEY = AIzaSyDurj...
✓ AGENT_SERVICE_QDRANT_URL = http://localhost:6333
✓ AGENT_SERVICE_VECTOR_COLLECTION = docs
...

================================================================================
RESUMEN
================================================================================
✓ Variables de entorno cargadas correctamente
✓ El servicio debería funcionar sin necesidad de 'export' manual
```

## Iniciar el Servicio

Simplemente ejecuta:

```bash
uv run uvicorn main:app --reload --port 8080
```

Las variables se cargan automáticamente. Deberías ver en los logs:

```
2025-11-01 19:48:13,664 - main - INFO - Iniciando carga de variables de entorno...
2025-11-01 19:48:13,664 - infra.env - INFO - ✓ Cargando variables desde: /path/to/.env
2025-11-01 19:48:13,664 - infra.env - INFO - Variables cargadas desde 1 archivo(s)
```

## Troubleshooting

### "No se encontraron archivos .env"

**Causa**: El archivo `.env` no existe en la raíz del proyecto.

**Solución**:
```bash
cd agents-service
cp .env.example .env
# Edita .env con tus valores
```

### "VectorServiceClient requiere un nombre de colección"

**Causa**: La variable `VECTOR_SERVICE_COLLECTION_NAME` no está definida.

**Solución**:
```bash
# Agrega al .env:
VECTOR_SERVICE_COLLECTION_NAME=docs
```

### "WARNING - No se cargaron archivos .env" (pero el servicio funciona)

**Causa**: Las variables ya fueron cargadas en un import previo.

**Solución**: Esto es normal. El sistema usa un flag `_ENV_ALREADY_LOADED` para evitar recargas innecesarias.

### Variables no se reflejan después de cambios

**Causa**: El servidor está en modo `--reload` pero las variables ya fueron cargadas.

**Solución**: Reinicia manualmente el servidor con `Ctrl+C` y vuelve a iniciarlo.

## Variables Legacy vs. Nuevas

El sistema soporta dos nomenclaturas para compatibilidad:

| Variable Legacy | Variable Nueva | Uso |
|----------------|----------------|-----|
| `VECTOR_SERVICE_URL` | `AGENT_SERVICE_QDRANT_URL` | URL de Qdrant |
| `VECTOR_SERVICE_COLLECTION_NAME` | `AGENT_SERVICE_VECTOR_COLLECTION` | Nombre de colección |
| `EMBEDDING_MODEL` | `AGENT_DEFAULT_EMBEDDING_MODEL` | Modelo de embeddings |
| `EMBEDDING_BACKEND` | `AGENT_SERVICE_EMBEDDING_BACKEND` | Backend (fastembed/gemini) |

**Recomendación**: Usa las variables **legacy** (`VECTOR_SERVICE_*`) para mayor compatibilidad.

## Archivos Modificados

Los siguientes archivos fueron modificados para soportar carga automática:

1. **`infra/settings.py`**:
   - Usa ruta absoluta al `.env` del proyecto
   - Ya no depende del CWD (current working directory)

2. **`infra/env.py`**:
   - Agrega logging para mostrar qué archivos se cargan
   - Evita recargas innecesarias

3. **`agents_service/__init__.py`**:
   - Carga variables ANTES de importar submódulos
   - Garantiza que código al nivel de módulo tenga acceso a variables

4. **`main.py`**:
   - Configura logging antes de cargar variables
   - Muestra información sobre archivos cargados

## Buenas Prácticas

1. **Nunca commitees archivos `.env`**:
   - El `.gitignore` ya excluye `.env`
   - Usa `.env.example` como template

2. **Usa `.env.local` para overrides locales**:
   - No lo commitees
   - Se carga después de `.env`, permitiendo overrides

3. **No uses `export` manual**:
   - Ya no es necesario
   - Las variables se cargan automáticamente

4. **Verifica con el script de prueba**:
   - Ejecuta `uv run python scripts/test_env_loading.py`
   - Confirma que todas las variables están presentes

## Integración con IDEs

### VS Code

Agrega a `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--port",
        "8080"
      ],
      "jinja": true,
      "justMyCode": true,
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

**No necesitas** definir `envFile` porque el código carga `.env` automáticamente.

### PyCharm

Configura el run configuration:
- Script path: `uvicorn`
- Parameters: `main:app --reload --port 8080`
- Working directory: `/path/to/agents-service`

**No necesitas** agregar variables de entorno manualmente.
