# Repository Guidelines

## Project Structure & Module Organization
This Django backend lives under `backend/`, with `config/` holding global settings, URL routing, and ASGI/WSGI entrypoints. Domain logic and REST views sit in `users/`, which also owns `migrations/` (Supabase-managed) and `serializers.py`. Documentation references, including the data model, reside in `docs/`. Operational helpers—`manage.py`, `pyproject.toml`, `uv.lock`, and scripts under `scripts/`—coordinate the runtime, diagnostics, and dependency graph.

## Build, Test, and Development Commands
Use `uv` to manage the environment and keep dependencies consistent:
```bash
uv venv && source .venv/bin/activate
uv sync
uv run python manage.py runserver 0.0.0.0:8000
uv run python scripts/test_db_connection.py
```
Run health checks with `uv run python manage.py check` before opening pull requests, and prefer `uv run python manage.py shell_plus` for quick ORM exploration when django-extensions is installed locally.

## Coding Style & Naming Conventions
Target Python 3.13.7 and Django 5 patterns. Follow PEP 8 with 4-space indentation, `snake_case` for modules/functions, and `UpperCamelCase` for classes like `AppUser`. Keep docstrings descriptive and bilingual where existing modules already do so. Retain verbose `help_text` metadata on model fields so the admin and API docs remain informative, and avoid adding Django-managed migrations to Supabase tables marked `managed=False`.

## Testing Guidelines
Write unit tests alongside each app—in this codebase they live in `users/tests.py` or a `users/tests/` package. Base test cases on `django.test.TestCase`, mirror API paths in method names (e.g., `test_dashboard_users_returns_premium_flag`), and isolate Supabase-only features behind feature flags or fixtures. Execute suites with `uv run python manage.py test` and gather coverage via `uv run coverage run manage.py test` followed by `uv run coverage report`.

## Commit & Pull Request Guidelines
The repository has no public history yet; adopt Conventional Commits to keep future history searchable. Example: `feat(users): add premium tier filter`. Each PR should outline the problem, summarize the solution, list migrations or Supabase scripts touched, note environment variables, and paste the exact test commands run. Attach screenshots for API schema or admin UI changes and mention any follow-up tickets.

## Environment & Security Notes
Copy `.env.example` to `.env` and fill Supabase credentials with `python-decouple`-compatible keys. Rotate secrets outside of version control and never commit generated lockfiles with sensitive overrides. Because `AppUser` syncs from Supabase, skip `python manage.py migrate` for that table and run schema adjustments through Supabase migrations or SQL scripts instead. Always enable CORS hosts and `DEBUG` flags appropriately per environment when deploying.

- Configura `SUPABASE_JWT_SECRET` (el mismo que devuelve `supabase status -o env`) y, si lo prefieres, `SUPABASE_JWKS_URL` para validar tokens emitidos por Supabase Auth. El backend también acepta directamente los valores de `SUPABASE_SERVICE_ROLE_KEY` y `SUPABASE_SECRET_KEY` en el header `Authorization` cuando `SUPABASE_ALLOW_SERVICE_ROLE_BEARER=true`.
- El endpoint `POST /dashboard/users/provision/` crea usuarios directamente en Supabase Auth; define `SUPABASE_API_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_SECRET_KEY` y, opcionalmente, `SUPABASE_ADMIN_TIMEOUT` en tu `.env` antes de usarlo.
- Para gestionar roles rápidamente, usa `GET /dashboard/users/roles/`, `GET /dashboard/users/roles/{rol}/` y `POST /dashboard/users/{id}/set-role/` (este último requiere token `service_role`).
