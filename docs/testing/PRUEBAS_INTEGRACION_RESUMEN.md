# 🧪 Resumen de Pruebas de Integración - AURA360

Este documento proporciona un resumen ejecutivo del conjunto de pruebas de integración implementado para validar la arquitectura completa de AURA360.

## ✅ ¿Qué se ha implementado?

Se ha creado un **conjunto completo de pruebas de integración** que valida todos los puntos de conexión entre los servicios del ecosistema AURA360:

```
┌─────────────────────────────────────────────────────────────┐
│                    AURA360 Ecosystem                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Backend    │───▶│   Agentes    │───▶│   Vectorial  │ │
│  │   Django     │◀───│   FastAPI    │◀───│   FastAPI    │ │
│  │  (puerto     │    │  (puerto     │    │  (puerto     │ │
│  │   8000)      │    │   8080)      │    │   8001)      │ │
│  └──────────────┘    └──────────────┘    └──────────────┘ │
│        │                    │                    │          │
│        ▼                    ▼                    ▼          │
│   ✅ Pruebas          ✅ Pruebas          ✅ Pruebas        │
│   Backend             Agentes            Vectorial         │
│                                                             │
│                    ┌──────────────┐                        │
│                    │     E2E      │                        │
│                    │   Pruebas    │                        │
│                    │   Completas  │                        │
│                    └──────────────┘                        │
│                          ✅                                 │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Archivos Creados

```
AURA360/
│
├── vectorial_db/
│   └── tests/
│       └── integration/
│           └── test_vectorial_service_integration.py  ✅ NUEVO
│
├── agents-service/
│   └── tests/
│       └── integration/
│           └── test_agents_service_integration.py     ✅ NUEVO
│
├── backend/
│   └── holistic/
│       └── tests/
│           └── test_backend_integration.py            ✅ NUEVO
│
├── tests/
│   └── e2e/
│       ├── __init__.py                                ✅ NUEVO
│       ├── conftest.py                                ✅ NUEVO
│       └── test_full_integration_flow.py              ✅ NUEVO
│
├── scripts/
│   ├── README.md                                      ✅ NUEVO
│   └── run_integration_tests.sh                      ✅ NUEVO (ejecutable)
│
├── docs/
│   └── INTEGRATION_TESTING.md                         ✅ NUEVO
│
└── .env.integration_tests.example                     ✅ NUEVO
```

## 🎯 Cobertura de Pruebas

### 1️⃣ Servicio Vectorial (Qdrant + FastAPI)

**Archivo**: `vectorial_db/tests/integration/test_vectorial_service_integration.py`

**Pruebas**:
- ✅ Health check y métricas del sistema
- ✅ Ingesta de documentos (individual y batch)
- ✅ Búsqueda semántica básica
- ✅ Búsqueda con filtros de categoría
- ✅ Endpoints del DLQ (Dead Letter Queue)

**Comando**:
```bash
cd vectorial_db
pytest tests/integration/test_vectorial_service_integration.py -v
```

---

### 2️⃣ Servicio de Agentes (FastAPI + Google ADK)

**Archivo**: `agents-service/tests/integration/test_agents_service_integration.py`

**Pruebas**:
- ✅ Generación de recomendaciones por categoría (mind, body, soul, holistic)
- ✅ Soporte de aliases en español (mente, cuerpo, alma)
- ✅ Información de consultas vectoriales en respuesta
- ✅ Manejo de errores (categoría no soportada, campos faltantes)
- ✅ Validación de latencia y performance

**Comando**:
```bash
cd agents-service
pytest tests/integration/test_agents_service_integration.py -v
```

---

### 3️⃣ Backend Django

**Archivo**: `backend/holistic/tests/test_backend_integration.py`

**Pruebas**:
- ✅ Comunicación Backend → Servicio de Agentes
- ✅ Persistencia de HolisticRequest, HolisticAgentRun, HolisticVectorQuery
- ✅ Manejo de timeouts y errores HTTP
- ✅ Validación de perfiles de agentes (HolisticAgentProfile)
- ✅ Pruebas end-to-end del endpoint API

**Comando**:
```bash
cd backend
pytest holistic/tests/test_backend_integration.py -v
```

---

### 4️⃣ Pruebas End-to-End Completas

**Archivo**: `tests/e2e/test_full_integration_flow.py`

**Pruebas**:
- ✅ Flujo completo Cliente → Backend → Agentes → Vector DB → Respuesta
- ✅ Ingesta de documentos + búsqueda + generación de recomendaciones
- ✅ Validación de todas las categorías
- ✅ Manejo de errores y autenticación
- ✅ Pruebas de performance con solicitudes concurrentes

**Comando**:
```bash
# Desde la raíz del proyecto
pytest tests/e2e/test_full_integration_flow.py -v
```

---

## 🚀 Inicio Rápido

### Paso 1: Iniciar Todos los Servicios

```bash
# Terminal 1: Servicio Vectorial
cd vectorial_db
docker compose up -d

# Terminal 2: Servicio de Agentes
cd agents-service
uv run uvicorn main:app --reload --port 8080

# Terminal 3: Backend Django
cd backend
uv run python manage.py runserver
```

### Paso 2: Verificar que los Servicios Estén Corriendo

```bash
# Servicio Vectorial
curl http://localhost:8001/readyz

# Servicio de Agentes
curl http://localhost:8080/readyz

# Backend Django
curl http://localhost:8000/api/health
```

### Paso 3: Ejecutar las Pruebas

#### Opción A: Script de Orquestación (Recomendado)

```bash
# Ejecutar TODAS las pruebas
./scripts/run_integration_tests.sh

# Con cobertura de código
./scripts/run_integration_tests.sh --coverage

# Solo una suite específica
./scripts/run_integration_tests.sh --only-vectorial
./scripts/run_integration_tests.sh --only-agents
./scripts/run_integration_tests.sh --only-backend
./scripts/run_integration_tests.sh --only-e2e
```

#### Opción B: Ejecutar Manualmente

```bash
# 1. Pruebas del Servicio Vectorial
cd vectorial_db
pytest tests/integration/test_vectorial_service_integration.py -v

# 2. Pruebas del Servicio de Agentes
cd agents-service
pytest tests/integration/test_agents_service_integration.py -v

# 3. Pruebas del Backend
cd backend
pytest holistic/tests/test_backend_integration.py -v

# 4. Pruebas End-to-End
cd ..  # Volver a la raíz
pytest tests/e2e/test_full_integration_flow.py -v
```

---

## 📊 Reportes y Salida

### Reportes JUnit XML

El script de orquestación genera reportes XML en formato JUnit:

```
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

# Ver reporte HTML
open htmlcov/index.html
```

### Salida del Script

El script proporciona output colorizado y detallado:

```
═══════════════════════════════════════════════════════════════
  AURA360 - Suite de Pruebas de Integración
═══════════════════════════════════════════════════════════════

ℹ Directorio del proyecto: /Users/freakscode/Proyectos 2025/AURA360
ℹ Directorio de reportes: test-reports/20251027_143022

═══════════════════════════════════════════════════════════════
  Verificando Prerequisitos
═══════════════════════════════════════════════════════════════

✓ Python 3 está instalado: Python 3.13.7
✓ uv está instalado: uv 0.5.11
✓ pytest está instalado

═══════════════════════════════════════════════════════════════
  Verificando Servicios
═══════════════════════════════════════════════════════════════

✓ Servicio Vectorial está disponible en http://localhost:8001/readyz
✓ Servicio de Agentes está disponible en http://localhost:8080/readyz
✓ Backend Django está disponible en http://localhost:8000/api/health
✓ Todos los servicios están disponibles

...
```

---

## 🔧 Configuración de Variables de Entorno

### Archivo de Ejemplo Creado

Se ha creado `.env.integration_tests.example` con todas las variables necesarias.

### Configuración Básica

```bash
# Copiar archivo de ejemplo
cp .env.integration_tests.example .env.integration_tests

# Editar con tus valores
nano .env.integration_tests
```

**Variables Críticas**:

```bash
# Google API Key (requerido para agentes)
GOOGLE_API_KEY=your-google-api-key-here

# Supabase (si usas Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# URLs de servicios
BACKEND_URL=http://localhost:8000
AGENTS_SERVICE_URL=http://localhost:8080
VECTORIAL_SERVICE_URL=http://localhost:8001
```

---

## 📚 Documentación Detallada

Toda la documentación detallada está disponible en:

### 📖 [docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md)

Este documento incluye:

- ✅ Arquitectura del sistema detallada
- ✅ Prerequisitos completos
- ✅ Instalación paso a paso
- ✅ Descripción de cada suite de pruebas
- ✅ Solución de problemas comunes
- ✅ Mejores prácticas
- ✅ Métricas y reporting

---

## 🎯 Casos de Uso

### Desarrollador Local

```bash
# Antes de hacer commit
./scripts/run_integration_tests.sh

# Solo probar lo que cambié (ej: backend)
./scripts/run_integration_tests.sh --only-backend
```

### CI/CD Pipeline

```bash
# En tu pipeline de CI
./scripts/run_integration_tests.sh --coverage
```

### QA / Testing

```bash
# Ejecutar todas las pruebas con output verbose
./scripts/run_integration_tests.sh --verbose --coverage
```

### Debugging

```bash
# Ejecutar solo una suite específica con pytest directamente
cd vectorial_db
pytest tests/integration/test_vectorial_service_integration.py -v -s -k "test_health_check"
```

---

## 🐛 Solución Rápida de Problemas

### Problema: "El servicio X no está disponible"

```bash
# Verificar que el servicio esté corriendo
lsof -i :8001  # Vectorial
lsof -i :8080  # Agentes
lsof -i :8000  # Backend

# Reiniciar servicios
cd vectorial_db && docker compose restart
cd agents-service && uv run uvicorn main:app --reload --port 8080
cd backend && uv run python manage.py runserver
```

### Problema: "Tests fallan por timeout"

```bash
# Aumentar timeouts en variables de entorno
export TEST_REQUEST_TIMEOUT=180
export HOLISTIC_AGENT_REQUEST_TIMEOUT=180

# O editar directamente en los archivos de prueba
```

### Problema: "No hay perfiles de agentes"

```bash
cd backend
uv run python manage.py shell -c "
from holistic.models import HolisticAgentProfile
for category in ['mind', 'body', 'soul', 'holistic']:
    HolisticAgentProfile.objects.get_or_create(
        category=category,
        defaults={
            'primary_agent': f'{category}_guardian',
            'fallback_agents': [],
            'embedding_model': 'text-embedding-3-small',
            'prompt_template': 'Default',
            'version': '1.0.0',
            'is_active': True,
        }
    )
"
```

---

## 📈 Métricas Esperadas

### Latencia

- **Servicio Vectorial**: < 100ms por búsqueda
- **Servicio de Agentes**: 2-30s (depende de LLM)
- **Backend**: 2-30s (depende de agentes)
- **E2E Completo**: < 60s

### Cobertura

- **Objetivo**: > 80% cobertura en todos los servicios
- **Crítico**: 100% en paths principales

---

## ✅ Checklist de Validación

Antes de considerar las pruebas exitosas, verificar:

- [ ] Todos los servicios están corriendo
- [ ] Variables de entorno configuradas correctamente
- [ ] Base de datos de prueba creada
- [ ] Perfiles de agentes creados en Django
- [ ] Colección de Qdrant existe y es accesible
- [ ] Google API Key configurada y válida
- [ ] Todos los tests pasan (verde)
- [ ] No hay errores en logs de servicios
- [ ] Reportes generados correctamente

---

## 🎓 Próximos Pasos

### Para Desarrollo

1. Agregar pruebas específicas para nuevas features
2. Aumentar cobertura de casos de borde
3. Agregar pruebas de carga/performance
4. Integrar con CI/CD pipeline

### Para Producción

1. Configurar ambiente de staging
2. Ejecutar pruebas contra staging antes de deploy
3. Monitorear métricas de latencia y error rate
4. Configurar alertas basadas en fallos de tests

---

## 📞 Soporte

Si encuentras problemas:

1. Consulta [INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md)
2. Revisa los logs de cada servicio
3. Verifica las variables de entorno
4. Ejecuta con `--verbose` para más detalle

---

## 🙏 Resumen

Se ha implementado un **conjunto completo de pruebas de integración** que:

✅ **Valida** todos los puntos de conexión entre servicios  
✅ **Automatiza** la ejecución con un script de orquestación  
✅ **Documenta** cada aspecto del sistema de pruebas  
✅ **Proporciona** reportes detallados en múltiples formatos  
✅ **Facilita** el debugging con mensajes claros  
✅ **Soporta** CI/CD y desarrollo local  

**Estado**: ✅ Listo para usar

**Última actualización**: Octubre 27, 2025

---

## 📝 Comandos Principales de Referencia Rápida

```bash
# Ejecutar TODAS las pruebas
./scripts/run_integration_tests.sh

# Ejecutar con cobertura
./scripts/run_integration_tests.sh --coverage

# Solo una suite
./scripts/run_integration_tests.sh --only-vectorial
./scripts/run_integration_tests.sh --only-agents
./scripts/run_integration_tests.sh --only-backend
./scripts/run_integration_tests.sh --only-e2e

# Verbose mode
./scripts/run_integration_tests.sh --verbose

# Ver ayuda
./scripts/run_integration_tests.sh --help

# Ejecutar manualmente (ejemplo)
cd vectorial_db
pytest tests/integration/test_vectorial_service_integration.py -v
```

---

**¡Feliz Testing! 🎉**

