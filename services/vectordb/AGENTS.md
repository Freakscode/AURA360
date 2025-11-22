# Repository Guidelines

## Project Structure & Module Organization
- `vectosvc/` holds the service code: `api/http.py` exposes FastAPI routes, `core/` drives ingestion and search pipelines, and `worker/tasks.py` defines Celery jobs.
- `tests/` bundles quick unit suites (`tests/unit/`) and Docker-backed integration suites (`tests/integration/`); shared fixtures live in `tests/conftest.py`.
- `scripts/` provides operational helpers like `ingest_batch.py` and Sci-Hub tooling—check `scripts/README.md` before modifying or adding runners.
- `documentation/` stores implementation plans and quickstarts; read `documentation/QUICKSTART.md` when iterating on ingest or search flows.
- `config/topics.yaml` tracks the biomedical taxonomy; update it alongside schema changes and note adjustments in pull requests.

## Build, Test, and Development Commands
- `pip install -e '.[dev]'` installs runtime plus dev extras; run inside a virtualenv or `uv` environment.
- `docker compose up -d` boots API, worker, Qdrant, Redis, and GROBID; pair with `docker compose logs -f api worker` while debugging.
- `pytest tests/ -v` executes the full suite; stop services with `docker compose stop` to release local resources.

## Coding Style & Naming Conventions
- Target Python 3.11+, follow PEP 8 with 4-space indentation, `snake_case` functions, and `PascalCase` models; keep module names lowercase to match existing packages.
- Add type hints on public functions and prefer Pydantic models for request/response schemas.
- Use `loguru` for structured logging and align logger names with module paths (e.g., `vectosvc.core.pipeline`).
- Configuration constants belong in `vectosvc/config.py` or environment variables; avoid hardcoded paths or credentials.

## Testing Guidelines
- Place fast, isolated tests under `tests/unit/` and avoid external services.
- Run integration suites under `tests/integration/` with the compose stack active; seed sample data via `scripts/ingest_test_papers.py` when validating ingestion flows.
- Name tests descriptively (`test_<component>_<condition>`) and cover edge cases for DLQ handling, caching, and retry logic.
- Enforce coverage with `pytest tests/ --cov=vectosvc --cov-report=html`; share coverage diffs in pull requests that touch core pipeline code.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `chore:`), mirroring the existing `feat: Complete vectorial database service with Sci-Hub integration` style.
- Reference related Jira or GitHub issues when available and keep subject lines under 72 characters.
- Provide PR descriptions with scope, test commands/output, and affected services; include curl snippets or screenshots for API changes.
- Keep secrets in `.env`, document new variables, and request reviewers familiar with impacted modules.
