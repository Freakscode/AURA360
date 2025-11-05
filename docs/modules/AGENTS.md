# Repository Guidelines

## Project Structure & Module Organization
- `aura_mobile/`: Flutter client; features in `lib/features`, shared UI in `lib/shared`, assets in `assets/`, tests in `test/` and `integration_test/`, env templates under `env/`.
- `backend/`: Django REST API; settings in `config/`, domain logic and tests in `users/`, helper scripts in `scripts/`, extended docs under `docs/`.
- `vectorial_db/`: FastAPI + Celery vector service; core code in `vectosvc/`, Docker stack in `docker-compose.yml`, tests split into `tests/unit` and `tests/integration`.
- Each module ships a detailed `AGENTS.md`; read the local guide before large refactors.

## Build, Test, and Development Commands
- Backend: `uv sync`, `uv run python manage.py runserver`, `uv run python manage.py test`, plus `uv run python scripts/test_db_connection.py` to confirm Supabase access.
- Mobile: `flutter pub get`, `flutter analyze`, `flutter test`, and `tool/run_dev.sh [--lan ...]` to load `env/local.env` when running on devices.
- Vector service: `uv sync` (or `pip install -e '.[dev]'`), `docker compose up -d`, `pytest tests/ -v --cov=vectosvc`, and `docker compose stop` when finished.

## Coding Style & Naming Conventions
- Python code follows PEP 8, 4-space indent, `snake_case` modules, `PascalCase` models, and typed public APIs; keep configuration in environment variables or `vectosvc/config.py`.
- Flutter code stays `dart format` clean, uses 2-space indentation, `snake_case.dart` filenames, `PascalCase` classes, `Provider` suffix for Riverpod providers, and `Page`/`View` for screens.
- Keep docs and comments concise, English-first, and colocated with the code they describe.

## Testing Guidelines
- Mirror source paths (`backend/users/tests`, `aura_mobile/test`, `vectorial_db/tests/unit`) and place cross-service flows in integration suites with the required services running.
- Capture coverage before PRs using `uv run python manage.py test --verbosity 2`, `pytest --cov=vectosvc`, and `flutter test --coverage`.
- Use `vectorial_db/scripts/ingest_test_papers.py` to seed sample documents when validating ingestion or search behaviour.

## Commit & Pull Request Guidelines
- Use Conventional Commits (`feat(api):`, `fix(mobile):`, `chore(vectosvc):`) and keep each commit focused on one concern.
- Update docs, env samples, or migrations alongside code; avoid drive-by formatting.
- PRs should include scope, linked issues, test output, and UI screenshots or screen recordings for Flutter changes; tag module owners when touching their area.

## Security & Configuration Tips
- Bootstrap env files (`backend/.env.example`, `aura_mobile/env/local.env.example`) and never commit real secrets.
- Configure `backend/SUPABASE_JWT_SECRET` with the Supabase JWT secret so the API can validate mobile bearer tokens.
- When using `tool/run_dev.sh --lan`, align backend and vector service endpoints in the mobile env file.
- The vector stack relies on Qdrant, Redis, and GROBID via Docker; mount Google Cloud credentials externally and document new environment variables in module guides.
