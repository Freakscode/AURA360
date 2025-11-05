# Guía de Pruebas de Integración - AURA360

Esta guía detalla cómo ejecutar y mantener las pruebas de integración del ecosistema completo de AURA360.

## 📋 Tabla de Contenidos

- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Prerequisitos](#prerequisitos)
- [Instalación y Configuración](#instalación-y-configuración)
- [Ejecución de Pruebas](#ejecución-de-pruebas)
- [Suites de Pruebas](#suites-de-pruebas)
- [Solución de Problemas](#solución-de-problemas)
- [Mejores Prácticas](#mejores-prácticas)

---

## 🏗️ Arquitectura del Sistema

El ecosistema AURA360 consta de tres servicios principales que se integran para proporcionar recomendaciones holísticas personalizadas:

```
┌─────────────┐
│   Cliente   │
│  (Mobile)   │
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────┐
│      Backend Django              │
│  - Autenticación                 │
│  - Orquestación                  │
│  - Persistencia                  │
└──────┬───────────────────────────┘
       │
       ↓
┌──────────────────────────────────┐
│   Servicio de Agentes (FastAPI) │
│  - Google ADK Agents             │
│  - Lógica de recomendaciones     │
│  - Consultas vectoriales         │
└──────┬───────────────────────────┘
       │
       ↓
┌──────────────────────────────────┐
│  Servicio Vectorial (FastAPI)   │
│  - Qdrant (base vectorial)       │
│  - Ingesta de documentos         │
│  - Búsqueda semántica            │
└──────────────────────────────────┘
```

### Flujo de Datos

1. **Cliente → Backend**: El cliente (app móvil) envía una solicitud de consejo holístico
2. **Backend → Agentes**: El backend orquesta la llamada al servicio de agentes
3. **Agentes → Vector DB**: El servicio de agentes consulta la base vectorial para contexto
4. **Agentes → Backend**: Los agentes generan recomendaciones y las retornan
5. **Backend → Cliente**: El backend persiste y retorna la respuesta al cliente

---

## 📦 Prerequisitos

### Software Requerido

- **Python 3.11+**: Lenguaje principal
- **uv**: Gestor de dependencias (recomendado) o `pip`
- **Docker & Docker Compose**: Para el servicio vectorial
- **PostgreSQL/Supabase**: Base de datos del backend
- **pytest**: Framework de pruebas

### Variables de Entorno

#### Backend Django (`backend/.env`)

```bash
# Base de datos
DATABASE_URL=postgresql://user:pass@localhost:5432/aura360
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Servicio de Agentes
HOLISTIC_AGENT_SERVICE_URL=http://localhost:8080/api/v1/holistic/advice
HOLISTIC_AGENT_SERVICE_TOKEN=optional-bearer-token
HOLISTIC_AGENT_REQUEST_TIMEOUT=120
```

#### Servicio de Agentes (`agents-service/.env`)

```bash
# Servicio Vectorial
AGENT_SERVICE_QDRANT_URL=http://localhost:6333
AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents
AGENT_SERVICE_TIMEOUT=30

# Embeddings
AGENT_DEFAULT_EMBEDDING_MODEL=text-embedding-3-small
GOOGLE_API_KEY=your-google-api-key

# Configuración
AGENT_SERVICE_MODEL_VERSION=1.0.0
```

#### Servicio Vectorial (`vectorial_db/.env`)

```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=holistic_agents

# Redis (para caché)
REDIS_URL=redis://localhost:6379/0

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

---

## 🚀 Instalación y Configuración

### 1. Configurar Servicio Vectorial

```bash
cd vectorial_db

# Iniciar servicios (Qdrant, Redis, GROBID, API, Worker)
docker compose up -d

# Verificar que estén corriendo
docker compose ps

# Verificar salud del servicio
curl http://localhost:8001/readyz
```

### 2. Configurar Servicio de Agentes

```bash
cd agents-service

# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Iniciar servicio
uv run uvicorn main:app --reload --port 8080
```

### 3. Configurar Backend Django

```bash
cd backend

# Instalar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# Ejecutar migraciones
uv run python manage.py migrate

# Crear perfiles de agentes
uv run python manage.py shell -c "
from holistic.models import HolisticAgentProfile
for category in ['mind', 'body', 'soul', 'holistic']:
    HolisticAgentProfile.objects.get_or_create(
        category=category,
        defaults={
            'primary_agent': f'{category}_guardian',
            'fallback_agents': [],
            'embedding_model': 'text-embedding-3-small',
            'prompt_template': 'Default template',
            'version': '1.0.0',
            'is_active': True,
        }
    )
"

# Iniciar servidor
uv run python manage.py runserver
```

### 4. Ingestar Datos de Prueba

```bash
cd vectorial_db

# Ingestar documentos de ejemplo
uv run python scripts/ingest_test_papers.py

# O usar el API directamente
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test-meditation-001",
    "text": "La meditación mindfulness mejora la salud mental y reduce el estrés...",
    "metadata": {
      "category": "mind",
      "topic": "meditation",
      "language": "es"
    }
  }'
```

---

## 🧪 Ejecución de Pruebas

### Método Rápido: Script de Orquestación

El script `run_integration_tests.sh` ejecuta todas las pruebas en orden:

```bash
# Desde la raíz del proyecto
./scripts/run_integration_tests.sh
```

#### Opciones del Script

```bash
# Solo servicio vectorial
./scripts/run_integration_tests.sh --only-vectorial

# Solo servicio de agentes
./scripts/run_integration_tests.sh --only-agents

# Solo backend
./scripts/run_integration_tests.sh --only-backend

# Solo end-to-end
./scripts/run_integration_tests.sh --only-e2e

# Con cobertura de código
./scripts/run_integration_tests.sh --coverage

# Modo verbose
./scripts/run_integration_tests.sh --verbose

# Omitir verificación de servicios
./scripts/run_integration_tests.sh --skip-setup
```

### Método Manual: Ejecutar Suites Individualmente

#### 1. Pruebas del Servicio Vectorial

```bash
cd vectorial_db

# Asegurarse de que los servicios estén corriendo
docker compose up -d

# Ejecutar pruebas
pytest tests/integration/test_vectorial_service_integration.py -v

# Con cobertura
pytest tests/integration/test_vectorial_service_integration.py -v \
  --cov=vectosvc --cov-report=html
```

#### 2. Pruebas del Servicio de Agentes

```bash
cd agents-service

# Asegurarse de que el servicio esté corriendo
uv run uvicorn main:app --reload --port 8080 &

# Ejecutar pruebas
pytest tests/integration/test_agents_service_integration.py -v

# Con cobertura
pytest tests/integration/test_agents_service_integration.py -v \
  --cov=agents_service --cov-report=html
```

#### 3. Pruebas del Backend

```bash
cd backend

# Asegurarse de que el backend esté corriendo
uv run python manage.py runserver &

# Ejecutar pruebas
pytest holistic/tests/test_backend_integration.py -v

# Con cobertura
pytest holistic/tests/test_backend_integration.py -v \
  --cov=holistic --cov-report=html
```

#### 4. Pruebas End-to-End

```bash
# Desde la raíz del proyecto
# Asegurarse de que TODOS los servicios estén corriendo

pytest tests/e2e/test_full_integration_flow.py -v

# Con cobertura
pytest tests/e2e/test_full_integration_flow.py -v \
  --cov --cov-report=html
```

---

## 📊 Suites de Pruebas

### 1. Servicio Vectorial (`test_vectorial_service_integration.py`)

**Ubicación**: `vectorial_db/tests/integration/`

**Pruebas incluidas**:

- ✅ Health check y métricas del sistema
- ✅ Ingesta de documentos individuales
- ✅ Ingesta batch de documentos
- ✅ Búsqueda semántica básica
- ✅ Búsqueda con filtros de categoría
- ✅ Endpoints del DLQ (Dead Letter Queue)

**Comandos**:

```bash
cd vectorial_db
pytest tests/integration/test_vectorial_service_integration.py -v
```

**Duración esperada**: ~30-60 segundos

---

### 2. Servicio de Agentes (`test_agents_service_integration.py`)

**Ubicación**: `agents-service/tests/integration/`

**Pruebas incluidas**:

- ✅ Generación de recomendaciones por categoría (mind, body, soul, holistic)
- ✅ Soporte de aliases en español
- ✅ Información de consultas vectoriales en respuesta
- ✅ Manejo de errores (categoría no soportada, campos faltantes)
- ✅ Validación de latencia y performance

**Comandos**:

```bash
cd agents-service
pytest tests/integration/test_agents_service_integration.py -v
```

**Duración esperada**: ~2-5 minutos (depende de LLMs)

---

### 3. Backend Django (`test_backend_integration.py`)

**Ubicación**: `backend/holistic/tests/`

**Pruebas incluidas**:

- ✅ Comunicación Backend → Servicio de Agentes
- ✅ Persistencia de registros (HolisticRequest, HolisticAgentRun)
- ✅ Persistencia de consultas vectoriales
- ✅ Manejo de timeouts y errores HTTP
- ✅ Validación de perfiles de agentes
- ✅ Pruebas end-to-end del endpoint API

**Comandos**:

```bash
cd backend
pytest holistic/tests/test_backend_integration.py -v
```

**Duración esperada**: ~2-5 minutos

---

### 4. End-to-End (`test_full_integration_flow.py`)

**Ubicación**: `tests/e2e/`

**Pruebas incluidas**:

- ✅ Flujo completo Cliente → Backend → Agentes → Vector DB
- ✅ Validación de categorías (mind, body, soul, holistic)
- ✅ Búsqueda vectorial con datos ingestados
- ✅ Manejo de errores y autenticación
- ✅ Pruebas de performance con solicitudes concurrentes

**Comandos**:

```bash
# Desde la raíz del proyecto
pytest tests/e2e/test_full_integration_flow.py -v
```

**Duración esperada**: ~5-10 minutos

---

## 🔧 Solución de Problemas

### Problema: "El servicio vectorial no está disponible"

**Solución**:

```bash
cd vectorial_db
docker compose up -d
docker compose logs -f api
```

Verificar que el puerto 8001 esté libre:

```bash
lsof -i :8001
```

---

### Problema: "El servicio de agentes no responde"

**Solución**:

```bash
cd agents-service

# Verificar que GOOGLE_API_KEY esté configurada
echo $GOOGLE_API_KEY

# Reiniciar el servicio
uv run uvicorn main:app --reload --port 8080
```

Verificar logs del servicio para errores de API key.

---

### Problema: "Error de conexión a Qdrant"

**Solución**:

```bash
cd vectorial_db

# Verificar que Qdrant esté corriendo
docker compose ps

# Reiniciar Qdrant si es necesario
docker compose restart qdrant

# Verificar colección
curl http://localhost:6333/collections/holistic_agents
```

---

### Problema: "Tests fallan por timeout"

**Solución**:

Aumentar los timeouts en los archivos de prueba:

```python
# En test_*.py
TEST_TIMEOUT = 180  # Aumentar de 120 a 180 segundos
REQUEST_TIMEOUT = 180
```

O configurar variables de entorno:

```bash
export HOLISTIC_AGENT_REQUEST_TIMEOUT=180
export AGENT_SERVICE_TIMEOUT=60
```

---

### Problema: "No hay perfiles de agentes activos"

**Solución**:

```bash
cd backend

uv run python manage.py shell -c "
from holistic.models import HolisticAgentProfile
HolisticAgentProfile.objects.all().update(is_active=True)
"
```

---

### Problema: "Error de autenticación en pruebas E2E"

**Solución**:

Actualizar la fixture `auth_token` en `test_full_integration_flow.py`:

```python
@pytest.fixture(scope="module")
def auth_token() -> str:
    # Implementar tu lógica de autenticación aquí
    # Ejemplo con Supabase:
    response = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        json={
            "email": "test@example.com",
            "password": "testpass123",
        }
    )
    return response.json()["access_token"]
```

---

## 📝 Mejores Prácticas

### 1. Ejecutar Pruebas Antes de Commits

```bash
# Ejecutar suite completa
./scripts/run_integration_tests.sh

# O solo las pruebas relevantes a tu cambio
./scripts/run_integration_tests.sh --only-backend
```

### 2. Mantener Datos de Prueba Limpios

```bash
# Limpiar colección de prueba en Qdrant
curl -X DELETE http://localhost:6333/collections/holistic_agents_test
```

### 3. Usar Trace IDs Únicos

Todas las pruebas generan trace IDs únicos para facilitar el debugging:

```python
trace_id = f"test-{uuid.uuid4()}"
```

### 4. Monitorear Latencia

Las pruebas validan que las respuestas sean razonables:

```python
assert elapsed_ms < 120000  # Menos de 2 minutos
```

Ajustar estos valores según tu infraestructura.

### 5. Revisar Reportes de Cobertura

```bash
# Generar reporte HTML
pytest --cov --cov-report=html

# Abrir reporte
open htmlcov/index.html
```

### 6. Documentar Cambios en Pruebas

Al agregar nuevas pruebas, actualizar esta documentación con:

- Propósito de la prueba
- Prerequisitos específicos
- Duración esperada
- Casos de borde cubiertos

---

## 📈 Métricas y Reporting

### Reportes JUnit XML

El script de orquestación genera reportes XML:

```bash
test-reports/
└── 20251027_143022/
    ├── Servicio_Vectorial.xml
    ├── Servicio_de_Agentes.xml
    ├── Backend_Django.xml
    └── End-to-End.xml
```

### Cobertura de Código

```bash
# Generar reporte de cobertura
./scripts/run_integration_tests.sh --coverage

# Ver reporte en terminal
coverage report

# Generar HTML
coverage html
open htmlcov/index.html
```

### Métricas del Sistema

```bash
# Métricas del servicio vectorial
curl http://localhost:8001/metrics | jq

# DLQ stats
curl http://localhost:8001/dlq/stats | jq
```

---

## 🔗 Referencias

- [Documentación del Servicio Vectorial](../vectorial_db/documentation/QUICKSTART.md)
- [Documentación del Servicio de Agentes](../agents-service/README.md)
- [Documentación del Backend](../backend/docs/README.md)
- [AGENTS.md del Proyecto](../AGENTS.md)

---

## 🤝 Contribución

Al agregar nuevas pruebas:

1. Seguir la estructura existente
2. Usar nombres descriptivos
3. Documentar prerequisitos
4. Validar estructura completa de respuestas
5. Incluir casos de error
6. Medir y documentar latencia esperada

---

**Última actualización**: Octubre 2025  
**Versión del documento**: 1.0.0

