# ✅ Checklist de Pruebas de Integración - AURA360

Este documento proporciona un checklist paso a paso para ejecutar las pruebas de integración del ecosistema AURA360.

---

## 🎯 Antes de Comenzar

### Prerequisitos del Sistema

- [ ] Python 3.11+ instalado
- [ ] Docker y Docker Compose instalados
- [ ] `uv` o `pip` instalado
- [ ] Git repositorio clonado
- [ ] Conexión a internet estable

### Variables de Entorno

- [ ] Google API Key obtenida (para agentes)
- [ ] Supabase configurado (si aplica)
- [ ] Archivo `.env` creado en cada servicio

---

## 📦 Paso 1: Instalar Dependencias

### Servicio Vectorial

```bash
cd vectorial_db
uv sync
# o: pip install -e '.[dev]'
```

- [ ] Dependencias instaladas sin errores
- [ ] pytest disponible: `pytest --version`

### Servicio de Agentes

```bash
cd agents-service
uv sync
```

- [ ] Dependencias instaladas sin errores
- [ ] pytest disponible

### Backend Django

```bash
cd backend
uv sync
```

- [ ] Dependencias instaladas sin errores
- [ ] pytest y Django configurados

---

## 🚀 Paso 2: Iniciar Servicios

### 2.1 Servicio Vectorial

```bash
cd vectorial_db
docker compose up -d
```

**Verificaciones**:
- [ ] Containers corriendo: `docker compose ps`
- [ ] Qdrant accesible: `curl http://localhost:6333/readyz`
- [ ] Redis corriendo
- [ ] API corriendo: `curl http://localhost:8001/readyz`

**Logs**:
```bash
docker compose logs -f api
```

### 2.2 Servicio de Agentes

```bash
cd agents-service

# Configurar variable de entorno
export GOOGLE_API_KEY="tu-api-key"

# Iniciar servicio
uv run uvicorn main:app --reload --port 8080
```

**Verificaciones**:
- [ ] Servicio iniciado sin errores
- [ ] Health check: `curl http://localhost:8080/readyz`
- [ ] No hay errores de API key en logs

### 2.3 Backend Django

```bash
cd backend

# Ejecutar migraciones (primera vez)
uv run python manage.py migrate

# Crear perfiles de agentes (primera vez)
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

# Iniciar servidor
uv run python manage.py runserver
```

**Verificaciones**:
- [ ] Servidor corriendo en puerto 8000
- [ ] Base de datos conectada
- [ ] Perfiles de agentes creados
- [ ] Health check: `curl http://localhost:8000/api/health`

---

## 🧪 Paso 3: Ejecutar Pruebas

### Opción A: Script de Orquestación (Recomendado)

```bash
# Desde la raíz del proyecto
./scripts/run_integration_tests.sh
```

**Verificaciones**:
- [ ] Script inicia sin errores
- [ ] Todos los servicios detectados como disponibles
- [ ] Pruebas ejecutadas en orden
- [ ] Reportes generados en `test-reports/`

**Si alguna prueba falla**:
```bash
# Ejecutar solo la suite que falló
./scripts/run_integration_tests.sh --only-vectorial
./scripts/run_integration_tests.sh --only-agents
./scripts/run_integration_tests.sh --only-backend
./scripts/run_integration_tests.sh --only-e2e
```

### Opción B: Ejecución Manual

#### 3.1 Pruebas del Servicio Vectorial

```bash
cd vectorial_db
pytest tests/integration/test_vectorial_service_integration.py -v
```

**Tests esperados**:
- [ ] test_health_check - PASSED
- [ ] test_metrics_endpoint - PASSED
- [ ] test_ingest_single_document - PASSED
- [ ] test_ingest_batch_documents - PASSED
- [ ] test_basic_search - PASSED
- [ ] test_search_with_category_filter - PASSED
- [ ] test_dlq_stats_endpoint - PASSED
- [ ] test_dlq_list_endpoint - PASSED

**Total esperado**: ~8 tests, todos PASSED

#### 3.2 Pruebas del Servicio de Agentes

```bash
cd agents-service
pytest tests/integration/test_agents_service_integration.py -v
```

**Tests esperados**:
- [ ] test_generate_advice_by_category[mind] - PASSED
- [ ] test_generate_advice_by_category[body] - PASSED
- [ ] test_generate_advice_by_category[soul] - PASSED
- [ ] test_generate_advice_by_category[holistic] - PASSED
- [ ] test_advice_with_spanish_category_aliases - PASSED
- [ ] test_advice_includes_vector_query_info - PASSED
- [ ] test_unsupported_category_returns_422 - PASSED
- [ ] test_missing_required_fields_returns_422 - PASSED
- [ ] test_empty_user_profile_returns_422 - PASSED
- [ ] test_advice_latency_is_reasonable - PASSED

**Total esperado**: ~10 tests, todos PASSED

**Nota**: Estos tests pueden tardar varios minutos debido a LLMs.

#### 3.3 Pruebas del Backend

```bash
cd backend
pytest holistic/tests/test_backend_integration.py -v
```

**Tests esperados**:
- [ ] test_call_agent_service_success - PASSED
- [ ] test_holistic_request_creates_records - PASSED
- [ ] test_vector_queries_are_persisted - PASSED
- [ ] test_agent_service_timeout_is_handled - PASSED
- [ ] test_agent_service_http_error_is_handled - PASSED
- [ ] test_missing_agent_profile_returns_503 - PASSED
- [ ] test_fetch_user_profile_returns_complete_profile - PASSED
- [ ] test_create_agent_run_creates_record - PASSED
- [ ] test_end_to_end_advice_request - PASSED

**Total esperado**: ~9 tests, todos PASSED

#### 3.4 Pruebas End-to-End

```bash
# Desde la raíz del proyecto
pytest tests/e2e/test_full_integration_flow.py -v
```

**Tests esperados**:
- [ ] test_complete_advice_flow_mind_category - PASSED
- [ ] test_complete_advice_flow_holistic_category - PASSED
- [ ] test_vector_search_returns_relevant_results - PASSED
- [ ] test_invalid_category_returns_error - PASSED
- [ ] test_unauthorized_request_returns_401 - PASSED
- [ ] test_concurrent_requests_are_handled - PASSED

**Total esperado**: ~6 tests, todos PASSED

**Nota**: Estos tests pueden tardar más tiempo (5-10 minutos).

---

## 📊 Paso 4: Verificar Resultados

### Reportes JUnit XML

```bash
# Los reportes se encuentran en:
ls -la test-reports/$(ls -t test-reports/ | head -1)/

# Debería mostrar:
# - Servicio_Vectorial.xml
# - Servicio_de_Agentes.xml
# - Backend_Django.xml
# - End-to-End.xml
```

- [ ] Todos los archivos XML generados
- [ ] Sin errores en los reportes

### Cobertura de Código

Si ejecutaste con `--coverage`:

```bash
# Ver reporte en terminal
coverage report

# Abrir reporte HTML
open htmlcov/index.html
```

- [ ] Cobertura > 80% en servicios críticos
- [ ] Reporte HTML generado correctamente

### Logs de Servicios

Verificar que no hay errores críticos:

```bash
# Servicio Vectorial
docker compose logs api | grep ERROR

# Servicio de Agentes
# (revisar output del terminal donde corre)

# Backend Django
# (revisar output del terminal donde corre)
```

- [ ] Sin errores críticos en logs
- [ ] Solo warnings esperados (si los hay)

---

## 🔍 Paso 5: Validación Final

### Métricas del Sistema

```bash
# Métricas del servicio vectorial
curl http://localhost:8001/metrics | jq

# Verificar:
# - collection.total_points > 0
# - cache.hit_rate (si aplica)
# - pipeline stats
```

- [ ] Métricas responden correctamente
- [ ] Valores razonables

### Estado de Servicios

```bash
# Health checks finales
curl http://localhost:8001/readyz  # Vectorial
curl http://localhost:8080/readyz  # Agentes
curl http://localhost:8000/api/health  # Backend
```

- [ ] Todos los servicios responden OK
- [ ] Sin errores de timeout

---

## 🎉 Éxito Completo

Si todos los checks anteriores están marcados:

- ✅ **Servicios configurados correctamente**
- ✅ **Pruebas ejecutadas exitosamente**
- ✅ **Reportes generados**
- ✅ **Sin errores críticos**
- ✅ **Sistema validado y listo**

---

## 🐛 Troubleshooting

### Problema Común 1: Puerto Ocupado

**Síntoma**: "Address already in use" o "port is already allocated"

**Solución**:
```bash
# Encontrar proceso usando el puerto
lsof -i :8001  # o :8080, :8000

# Matar el proceso
kill -9 <PID>

# O cambiar el puerto del servicio
```

### Problema Común 2: Servicio Vectorial no Responde

**Solución**:
```bash
cd vectorial_db
docker compose down
docker compose up -d
docker compose logs -f api
```

### Problema Común 3: Google API Key Inválida

**Síntoma**: Errores de autenticación en servicio de agentes

**Solución**:
```bash
# Verificar que la variable esté configurada
echo $GOOGLE_API_KEY

# Exportarla si es necesario
export GOOGLE_API_KEY="tu-api-key-real"

# Reiniciar el servicio de agentes
```

### Problema Común 4: Base de Datos No Migrada

**Síntoma**: Errores de Django sobre tablas inexistentes

**Solución**:
```bash
cd backend
uv run python manage.py migrate
uv run python manage.py shell -c "..."  # Crear perfiles
```

### Problema Común 5: Timeout en Pruebas

**Solución**:
```bash
# Aumentar timeouts
export TEST_REQUEST_TIMEOUT=240
export HOLISTIC_AGENT_REQUEST_TIMEOUT=240

# Ejecutar nuevamente
./scripts/run_integration_tests.sh
```

---

## 📞 Siguientes Pasos

Una vez que todas las pruebas pasen:

1. **Commit de cambios** (si modificaste algo)
2. **Documentar** cualquier configuración especial
3. **Integrar** en CI/CD pipeline
4. **Monitorear** métricas en producción

---

## 📚 Documentación Completa

Para más detalles, consulta:

- [PRUEBAS_INTEGRACION_RESUMEN.md](PRUEBAS_INTEGRACION_RESUMEN.md) - Resumen ejecutivo
- [docs/INTEGRATION_TESTING.md](docs/INTEGRATION_TESTING.md) - Guía completa
- [scripts/README.md](scripts/README.md) - Documentación de scripts

---

**Fecha**: Octubre 27, 2025  
**Versión**: 1.0.0  
**Estado**: ✅ Completo

