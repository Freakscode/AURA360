# AURA365 Backend API

Django REST Framework backend used by the AURA365 platform. The service exposes user management endpoints backed by Supabase and is configured for Django 5.2 and Python 3.13.

## Documentation
- Comprehensive guide: `docs/guides/README.md`
- Quickstart walkthrough: `docs/guides/QUICKSTART.md`
- Spanish executive summary: `docs/guides/RESUMEN.md`
- Setup checklist: `docs/guides/SETUP_COMPLETE.md`
- Database reference: `docs/database_schema.md`

## Project Layout
```
backend/
├── config/           # Django project configuration
├── users/            # App logic, serializers, views, urls
├── scripts/          # Operational helpers (e.g., test_db_connection.py)
├── docs/             # Documentation and references
├── manage.py         # Django entry point
├── pyproject.toml    # Project metadata and dependencies
├── uv.lock           # Locked dependency set for uv
└── AGENTS.md         # Contributor guidance
```

## Common Commands
```bash
uv venv && source .venv/bin/activate
uv sync
uv run python manage.py runserver
uv run python scripts/test_db_connection.py
uv run python manage.py test

# Start Celery worker (queues api_default + holistic) from repo root
./scripts/run_celery.sh worker

# Start Celery beat scheduler
./scripts/run_celery.sh beat
```

> Nota: los comandos de Celery asumen que estás en la raíz del repositorio. Si ya estás dentro de `services/api`, ejecuta `../scripts/run_celery.sh worker` y ajusta las rutas según tu contexto.
