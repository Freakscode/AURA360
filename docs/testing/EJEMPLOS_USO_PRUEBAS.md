# 📖 Ejemplos de Uso - Pruebas de Integración AURA360

Este documento proporciona ejemplos prácticos y casos de uso reales para ejecutar las pruebas de integración.

---

## 🎬 Caso de Uso 1: Desarrollador Local - Primera Vez

**Escenario**: Acabas de clonar el repositorio y quieres validar que todo funcione.

### Pasos:

```bash
# 1. Clonar repositorio (si no lo has hecho)
git clone <repo-url>
cd AURA360

# 2. Configurar variables de entorno
cp .env.integration_tests.example .env.integration_tests
nano .env.integration_tests
# Agregar tu GOOGLE_API_KEY

# 3. Iniciar servicio vectorial
cd vectorial_db
docker compose up -d
cd ..

# 4. En una nueva terminal, iniciar servicio de agentes
cd agents-service
export GOOGLE_API_KEY="tu-api-key"
uv sync
uv run uvicorn main:app --reload --port 8080 &
cd ..

# 5. En otra terminal, iniciar backend
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py shell -c "
from holistic.models import HolisticAgentProfile
for category in ['mind', 'body', 'soul', 'holistic']:
    HolisticAgentProfile.objects.get_or_create(
        category=category,
        defaults={
            'primary_agent': f'{category}_guardian',
            'embedding_model': 'text-embedding-3-small',
            'version': '1.0.0',
            'is_active': True,
        }
    )
"
uv run python manage.py runserver &
cd ..

# 6. Ejecutar todas las pruebas
./scripts/run_integration_tests.sh
```

**Resultado Esperado**:
```
✓ Servicio Vectorial: PASSED
✓ Servicio de Agentes: PASSED
✓ Backend Django: PASSED
✓ End-to-End: PASSED

Todas las pruebas pasaron exitosamente ✓
```

---

## 🔄 Caso de Uso 2: Desarrollo Iterativo - Solo Backend

**Escenario**: Estás trabajando en el backend y quieres validar tus cambios sin ejecutar todo.

```bash
# Servicios ya corriendo (de sesión anterior)

# Ejecutar solo pruebas del backend
./scripts/run_integration_tests.sh --only-backend

# O directamente con pytest para más control
cd backend
pytest holistic/tests/test_backend_integration.py -v -k "test_holistic_request"
```

**Uso con pytest**:
```bash
# Ejecutar test específico
pytest holistic/tests/test_backend_integration.py::TestBackendAgentsServiceIntegration::test_call_agent_service_success -v

# Con output detallado
pytest holistic/tests/test_backend_integration.py -v -s

# Con cobertura solo del módulo holistic
pytest holistic/tests/test_backend_integration.py --cov=holistic --cov-report=term
```

---

## 🎯 Caso de Uso 3: Testing de Feature Nueva

**Escenario**: Agregaste una nueva categoría "nutrition" y quieres validarla.

### Paso 1: Crear Perfil de Agente

```bash
cd backend
uv run python manage.py shell -c "
from holistic.models import HolisticAgentProfile
HolisticAgentProfile.objects.create(
    category='nutrition',
    primary_agent='nutritional_guardian',
    fallback_agents=[],
    embedding_model='text-embedding-3-small',
    prompt_template='Nutrition template',
    version='1.0.0',
    is_active=True,
)
"
```

### Paso 2: Ingestar Documentos de Nutrición

```bash
cd vectorial_db
curl -X POST http://localhost:8001/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "nutrition-test-001",
    "text": "Una dieta balanceada incluye proteínas, carbohidratos complejos y grasas saludables...",
    "metadata": {
      "category": "nutrition",
      "topic": "balanced_diet",
      "language": "es"
    }
  }'
```

### Paso 3: Probar con curl

```bash
# Probar endpoint del backend directamente
curl -X POST http://localhost:8000/api/v1/holistic/advice \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <tu-token>" \
  -d '{
    "user_id": "test-user-123",
    "category": "nutrition",
    "metadata": {
      "context": "Necesito mejorar mis hábitos alimenticios"
    }
  }' | jq
```

### Paso 4: Agregar Test

Crear `test_nutrition.py`:

```python
def test_nutrition_category(self):
    """Valida que la nueva categoría nutrition funciona."""
    payload = {
        "user_id": str(self.user.id),
        "category": "nutrition",
        "metadata": {"test": True},
    }
    
    response = self.client.post("/api/v1/holistic/advice", payload, format="json")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert "nutrition" in str(data["result"])
```

---

## 🚨 Caso de Uso 4: Debugging de Fallo

**Escenario**: Un test falló y necesitas investigar qué pasó.

### Paso 1: Ejecutar con Verbose

```bash
./scripts/run_integration_tests.sh --verbose --only-agents
```

### Paso 2: Ejecutar Solo el Test que Falla

```bash
cd agents-service
pytest tests/integration/test_agents_service_integration.py::TestAdviceEndpoint::test_generate_advice_by_category -v -s --tb=long
```

### Paso 3: Revisar Logs de Servicios

```bash
# Logs del servicio vectorial
cd vectorial_db
docker compose logs api --tail=100

# Logs del servicio de agentes
# (ver output del terminal donde corre)

# Logs del backend
# (ver output del terminal donde corre)
```

### Paso 4: Ejecutar Manualmente la Solicitud

```bash
# Probar directamente el servicio de agentes
curl -X POST http://localhost:8080/api/v1/holistic/advice \
  -H "Content-Type: application/json" \
  -d '{
    "trace_id": "debug-test-001",
    "category": "mind",
    "user_profile": {
      "id": "test-user",
      "name": "Test User"
    }
  }' | jq
```

### Paso 5: Usar Python Debugger

Agregar breakpoint en el test:

```python
def test_generate_advice_by_category(self, ...):
    payload = {...}
    
    import pdb; pdb.set_trace()  # Breakpoint aquí
    
    response = requests.post(...)
```

Ejecutar:
```bash
pytest tests/integration/test_agents_service_integration.py::test_generate_advice_by_category -s
```

---

## 📊 Caso de Uso 5: CI/CD Pipeline

**Escenario**: Configurar pruebas en GitHub Actions / GitLab CI.

### GitHub Actions (`.github/workflows/integration-tests.yml`)

```yaml
name: Integration Tests

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Start Vectorial Service
        run: |
          cd vectorial_db
          docker compose up -d
          sleep 10
      
      - name: Start Agents Service
        run: |
          cd agents-service
          uv sync
          uv run uvicorn main:app --port 8080 &
          sleep 5
        env:
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      
      - name: Start Backend
        run: |
          cd backend
          uv sync
          uv run python manage.py migrate
          uv run python manage.py runserver &
          sleep 5
      
      - name: Run Integration Tests
        run: ./scripts/run_integration_tests.sh --coverage
      
      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

## ⏱️ Caso de Uso 6: Performance Testing

**Escenario**: Quieres medir el tiempo de respuesta del sistema.

### Script de Performance

```bash
# test_performance.sh
#!/bin/bash

echo "Testing performance..."

for i in {1..10}; do
    start=$(date +%s.%N)
    
    curl -s -X POST http://localhost:8000/api/v1/holistic/advice \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "user_id": "perf-test-user",
        "category": "mind",
        "metadata": {"test": true}
      }' > /dev/null
    
    end=$(date +%s.%N)
    duration=$(echo "$end - $start" | bc)
    
    echo "Request $i: ${duration}s"
done
```

### Ejecutar Performance Test

```bash
chmod +x test_performance.sh
export TOKEN="tu-token-aqui"
./test_performance.sh
```

---

## 🔐 Caso de Uso 7: Testing con Diferentes Usuarios

**Escenario**: Validar que diferentes tipos de usuarios obtienen respuestas apropiadas.

### Script de Testing Multi-Usuario

```python
# test_multi_user.py
import requests

BACKEND_URL = "http://localhost:8000"

test_users = [
    {
        "id": "user-beginner",
        "name": "Usuario Principiante",
        "age": 25,
        "experience_level": "beginner",
        "goals": ["reducir estrés", "mejorar sueño"],
    },
    {
        "id": "user-advanced",
        "name": "Usuario Avanzado",
        "age": 35,
        "experience_level": "advanced",
        "goals": ["optimizar performance", "mindfulness avanzado"],
    },
]

for user in test_users:
    print(f"\nTesting user: {user['name']}")
    
    response = requests.post(
        f"{BACKEND_URL}/api/v1/holistic/advice",
        json={
            "user_id": user["id"],
            "category": "mind",
            "metadata": {
                "user_profile": user,
            }
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Success: {len(data['result']['recommendations'])} recommendations")
        print(f"  Summary: {data['result']['summary'][:100]}...")
    else:
        print(f"✗ Failed: {response.status_code}")
```

---

## 📦 Caso de Uso 8: Testing de Batch Ingestion

**Escenario**: Validar la ingesta masiva de documentos.

```bash
cd vectorial_db

# Crear archivo de documentos
cat > test_batch.jsonl << EOF
{"doc_id": "batch-1", "text": "Documento 1...", "metadata": {"category": "mind"}}
{"doc_id": "batch-2", "text": "Documento 2...", "metadata": {"category": "body"}}
{"doc_id": "batch-3", "text": "Documento 3...", "metadata": {"category": "soul"}}
EOF

# Ingestar batch
uv run python scripts/ingest_batch.py test_batch.jsonl

# Verificar ingesta
curl http://localhost:8001/metrics | jq '.collection.total_documents'
```

---

## 🎨 Caso de Uso 9: Testing de Diferentes Idiomas

**Escenario**: Validar que el sistema funciona en español e inglés.

```python
# Test en español
response_es = client.post("/api/v1/holistic/advice", {
    "user_id": "test-user",
    "category": "mente",  # Español
    "metadata": {
        "context": "Necesito técnicas de relajación",
        "locale": "es-CO"
    }
})

# Test en inglés
response_en = client.post("/api/v1/holistic/advice", {
    "user_id": "test-user",
    "category": "mind",  # Inglés
    "metadata": {
        "context": "I need relaxation techniques",
        "locale": "en-US"
    }
})

assert response_es.status_code == 200
assert response_en.status_code == 200
```

---

## 🔍 Caso de Uso 10: Testing de Filtros Vectoriales

**Escenario**: Validar búsquedas con filtros específicos.

```bash
# Búsqueda con filtro de categoría y fecha
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "meditación mindfulness",
    "limit": 5,
    "filter": {
      "must": {
        "category": "mind",
        "language": "es"
      },
      "should": {
        "topic": "meditation"
      }
    }
  }' | jq
```

---

## 📝 Mejores Prácticas

### 1. Siempre Usar Trace IDs

```python
import uuid

trace_id = f"test-{uuid.uuid4()}"
payload = {
    "trace_id": trace_id,
    # ...
}
```

### 2. Limpiar Datos de Prueba

```bash
# Después de tests, limpiar colección de prueba
curl -X DELETE http://localhost:6333/collections/holistic_agents_test
```

### 3. Usar Fixtures de pytest

```python
@pytest.fixture(scope="module")
def test_user():
    user = create_test_user()
    yield user
    user.delete()
```

### 4. Parametrizar Tests

```python
@pytest.mark.parametrize("category,dimension", [
    ("mind", "mente"),
    ("body", "cuerpo"),
    ("soul", "alma"),
])
def test_category(category, dimension):
    # ...
```

---

## 🎓 Tips Avanzados

### Ejecutar Tests en Paralelo

```bash
# Instalar pytest-xdist
pip install pytest-xdist

# Ejecutar en paralelo
pytest tests/ -n 4  # 4 workers
```

### Generar Reporte HTML

```bash
pip install pytest-html

pytest tests/ --html=report.html --self-contained-html
```

### Usar Markers

```python
@pytest.mark.slow
def test_slow_operation():
    # ...

# Ejecutar solo tests rápidos
pytest -m "not slow"
```

---

**Última actualización**: Octubre 27, 2025  
**Versión**: 1.0.0

