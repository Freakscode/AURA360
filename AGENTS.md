# Repository Guidelines

## Project Structure & Modules
- `apps/mobile`: Flutter client; mirrors `lib/` ⇄ `test/`.
- `apps/web`: Angular 20 frontend with `.spec.ts` tests alongside features.
- `services/api`: Django REST API (Supabase-backed); manage via `services/api/manage.py`.
- `services/agents`: Google ADK + FastAPI; relies on Qdrant from `vectorial_db`.
- `services/vectordb`: Qdrant + FastAPI + Celery workers (Docker-first).
- `docs/`: Architecture, testing, and runbooks; update when behavior changes.

## Build, Test & Development Commands
- Agents:  
  ```bash
  cd services/agents
  uv sync
  uv run uvicorn main:app --reload --port 8080
  uv run pytest               # unit/integration tests
  ``` 
- API:  
  ```bash
  cd services/api
  uv sync
  uv run python manage.py runserver 0.0.0.0:8000
  uv run python manage.py test
  ```
- Vector DB:  
  ```bash
  cd services/vectordb
  docker compose up -d        # Qdrant, Redis, API, worker
  pytest tests/
  ```
- Web:  
  ```bash
  cd apps/web
  npm install
  ng serve
  ng test
  ```
- Mobile:  
  ```bash
  cd apps/mobile
  flutter pub get
  flutter run dev
  flutter test --coverage
  flutter analyze
  ```

## Coding Style & Naming
- Python: PEP8, 4 spaces; `snake_case` for functions/vars, `PascalCase` classes; type hints on public APIs; format with `black` + `ruff`.
- Dart/Flutter: 2 spaces; `snake_case.dart` filenames; run `dart format .` and `flutter analyze`.
- Angular/TypeScript: 2 spaces, single quotes, ~100-char lines; follow Angular Style Guide.
- Prefer small functions; colocate fixtures under `tests/` or `__tests__`.

## Testing Guidelines
- Add regression tests for every bug fix and new behavior.
- Mirror source paths when naming: `tests/feature_x/test_api.py`, `feature/thing.component.spec.ts`, `test/features/mood_controller_test.dart`.
- Keep tests deterministic; stub Qdrant/Supabase/Google ADK calls.
- Run the relevant suite before opening a PR.

## Commit & Pull Request Guidelines
- Commits use **Conventional Commits** with service scope, e.g., `feat(agents): add retrieval smoke test`, `fix(api): guard null supabase user`.
- PRs: clear summary, linked issue, screenshots for UI changes, tests run, note breaking changes.
- Keep PRs small and update docs when behavior shifts.

## Security & Configuration
- Never commit secrets; copy `.env.example` to `.env` per service.
- `services/agents` auto-loads env vars via `infra/env.py`; keep `.env` in that root.
- Verify vector store endpoints (`VECTOR_SERVICE_URL`, `docker compose ps` in `services/vectordb`).
- Prefer `.env.local` for overrides ignored by git.
