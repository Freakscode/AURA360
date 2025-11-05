# Guía de Pruebas del Backend

## Problema conocido con pytest

El backend tiene un problema conocido al usar `pytest` directamente debido a cómo pytest-django maneja las conexiones a Postgres cuando se crea la base de datos temporal. Después de crear `test_postgres`, la conexión se cierra y los tests que usan `setUpTestData` fallan con `psycopg2.InterfaceError: connection already closed`.

### Soluciones intentadas

1. ✅ Agregado `pytest-django>=4.9.0`
2. ✅ Configurado `CONN_MAX_AGE=0` en settings
3. ❌ Monkey-patching de `DatabaseWrapper.ensure_connection` (interfiere con pytest-django setup)
4. ❌ Fixture global de reconexión (no se ejecuta antes de `setUpTestData`)

## Solución recomendada: Django test runner

### Ejecutar todos los tests

```bash
cd backend
source .venv/bin/activate
uv run python manage.py test
```

### Ejecutar tests específicos

```bash
# Una app completa
uv run python manage.py test users

# Un archivo específico
uv run python manage.py test users.tests.test_quota

# Una clase específica
uv run python manage.py test users.tests.test_quota.CheckQuotaTests

# Un test específico
uv run python manage.py test users.tests.test_quota.CheckQuotaTests.test_seeded_tiers_exist
```

### Con cobertura

```bash
uv run coverage run --source='.' manage.py test
uv run coverage report
uv run coverage html  # Genera reporte en htmlcov/
```

### Con verbosidad

```bash
uv run python manage.py test --verbosity 2
```

## Estado actual ✅

- ✅ **25 tests unitarios pasan** con `uv run python manage.py test body users`
- ⏭️ **Tests de integración skip** cuando agents-service no está corriendo
- ❌ **Tests fallan con pytest** (problema conocido de conexión cerrada con pytest-django)

**Resultado de la última ejecución:**
```bash
Ran 25 tests in 2.007s
OK
```

Los tests funcionan perfectamente con `python manage.py test` porque Django's test runner maneja las conexiones de forma diferente y más robusta que pytest-django.

## Alternativa futura: SQLite para tests

Si se necesita velocidad en CI o desarrollo local, se puede configurar SQLite para tests:

```python
# En config/settings.py
import sys

TESTING = 'test' in sys.argv or 'pytest' in sys.modules

if TESTING and os.getenv('USE_SQLITE_TESTS', 'false').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
```

Luego ejecutar:
```bash
USE_SQLITE_TESTS=true uv run python manage.py test
```

## Contexto técnico

El stack de Supabase local está corriendo en Docker (`supabase_db_aura_mobile`) y es completamente funcional:
- PostgreSQL 17.6 en `localhost:54322`
- Health checks pasando
- La base `test_postgres` se crea y destruye correctamente

El problema es específico de cómo pytest-django interactúa con psycopg2 cuando cierra/reabre conexiones entre el setup de la base de prueba y la ejecución de `setUpTestData`.

