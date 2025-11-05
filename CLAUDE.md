# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AURA360 is a holistic wellness platform consisting of:
- **apps/mobile**: Flutter mobile client with mind/body/soul modules
- **services/api**: Django REST API for user management (Supabase-backed)
- **apps/web**: Angular 20 web frontend
- **services/agents**: Google ADK-based holistic agents (mind, body, soul) with vector retrieval
- **services/vectordb**: FastAPI + Celery + Qdrant vector database for biomedical document search

This is a **monorepo** with all applications and services organized under `/apps` and `/services` respectively.

## Development Commands

### Backend (Django)
```bash
cd services/api
uv sync
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py test
uv run python scripts/test_db_connection.py  # Verify Supabase connection
```

### Mobile (Flutter)
```bash
cd apps/mobile
flutter pub get
flutter analyze
flutter test --coverage

# Development with environment loading
export PATH="$PWD/tool:$PATH"
flutter run dev                    # Local env
flutter run dev --lan              # LAN mode for physical devices
```

**Environment Setup**: Copy `env/local.env.example` to `env/local.env` with your Supabase credentials. The `tool/run_dev.sh` helper automatically loads env vars via `--dart-define-from-file`.

### Frontend (Angular)
```bash
cd apps/web
npm install
ng serve                           # Dev server on http://localhost:4200
ng build
ng test
```

### Agents Service
```bash
cd services/agents
uv sync
uv run uvicorn main:app --reload --port 8080

# Test
uv run pytest
uv run python scripts/smoke_retrieval.py  # Validate vector retrieval
```

**Dependencies**: Requires `services/vectordb` services running for vector retrieval.

### Vector Database Service
```bash
cd services/vectordb
docker compose up -d               # Start Qdrant, Redis, GROBID, API, worker
docker compose logs -f api worker  # Monitor logs
docker compose stop

# Test
uv sync
pytest tests/ -v --cov=vectosvc

# Ingest documents
uv run python scripts/ingest_batch.py ./data/papers.jsonl
```

## Architecture Notes

### Mobile App Structure (Flutter)
- **Features**: Located in `lib/features/` with domain-driven modules:
  - `auth/`: Authentication flows
  - `rbac/`: Role-based access control
  - `mind/`: Mood tracker with tags and notes
  - `body/`: Physical activity, nutrition, sleep tracking
  - `soul/`: IKIGAI profile management
  - `user/`: User profile and psychosocial context
- **Core**: Infrastructure (network, storage, error handling) in `lib/core/`
- **App**: Configuration (routing, DI, theming, l10n) in `lib/app/`
- **State Management**: Riverpod providers with `Provider` suffix
- **Database**: Supabase via `lib/core/database/supabase_client.dart`

**Key Pattern**: Clean architecture with feature-based organization. Controllers handle business logic, repositories abstract data sources.

### Backend Structure (Django)
- **Apps**: `users/` contains models, serializers, views, and migrations
- **Config**: `config/` holds settings, URLs, WSGI/ASGI
- **Database**: Supabase-managed PostgreSQL; `AppUser` model uses `managed=False`
- **Auth**: JWT validation via `SUPABASE_JWT_SECRET` or `SUPABASE_JWKS_URL`

**Important**: Do NOT create migrations for Supabase-managed models. Schema changes go through Supabase migrations.

### Agents Service Architecture
- **Orchestration**: `api/routes.py` exposes `/api/v1/holistic/advice`
- **Agents**: Specialized agents in `holistic_agent/`, `nutritional_agent/`
- **Vector Store**: Qdrant integration via `services/vector_service.py`
- **Configuration**: Prefix variables with `AGENT_SERVICE_*` (see `infra/settings.py`)

**Integration**: Queries `vectorial_db` for RAG context using embeddings.

### Vector Database Architecture
- **API**: FastAPI routes in `vectosvc/api/http.py`
- **Pipeline**: Ingestion in `vectosvc/core/pipeline.py` with GROBID + PyMuPDF fallback
- **Worker**: Celery tasks in `vectosvc/worker/tasks.py`
- **Cache**: Redis caching for embeddings (90% speedup)
- **Topics**: 37 biomedical topics defined in `config/topics.yaml`

**Performance**: Embedding cache provides ~90% latency improvement (11.13s → 1.12s).

## Testing Guidelines

### Flutter Tests
- Mirror source paths under `test/` (e.g., `lib/features/auth` → `test/features/auth`)
- Integration tests in `integration_test/` using `testWidgets`
- Use Riverpod testing helpers for provider tests

### Python Tests (Backend & Services)
- Backend: `services/api/users/tests/`
- Vector DB: `services/vectordb/tests/unit/` (fast, isolated) and `services/vectordb/tests/integration/` (Docker-backed)
- Run integration tests with services running: `docker compose up -d`

### Angular Tests
- Jasmine + Karma test runner
- Run with `ng test`

## Environment & Configuration

### Common Environment Variables
```bash
# Backend
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=
DATABASE_URL=

# Mobile (env/local.env)
SUPABASE_URL=
SUPABASE_ANON_KEY=
DATABASE_DRIVER=postgres

# Agents Service
AGENT_SERVICE_QDRANT_URL=http://localhost:6333
AGENT_SERVICE_VECTOR_COLLECTION=holistic_agents
GOOGLE_API_KEY=

# Vector DB (in docker-compose.yml or .env)
QDRANT_URL=
REDIS_URL=
CELERY_BROKER_URL=
```

**Security**: Never commit `.env` files. Use `.env.example` templates.

## Package Management

- **Python services**: Use `uv` for dependency management (`uv sync`, `uv run`)
- **Flutter**: Standard `flutter pub get`
- **Angular**: Standard `npm install`

## Code Style

### Python
- PEP 8, 4-space indentation
- `snake_case` for modules/functions, `PascalCase` for classes
- Type hints on public APIs
- Structured logging with `loguru` (vector service) or Django logging

### Flutter/Dart
- `dart format .` with 2-space indentation
- `snake_case.dart` filenames, `PascalCase` classes, `camelCase` variables
- Resolve all analyzer warnings before committing
- Trailing commas on multiline arguments

### Angular/TypeScript
- Prettier config in `package.json`
- Follow Angular style guide
- 100 char line width, single quotes

## Commit Conventions

Use Conventional Commits format:
- `feat(module): description`
- `fix(module): description`
- `chore(module): description`

Modules: `mobile`, `backend`, `frontend`, `agents`, `vectosvc`, `api`, `core`, etc.

## Special Notes

### Supabase Integration
- Backend validates JWT tokens from mobile auth
- Mobile creates accounts that sync to backend `app_users` table via Supabase triggers
- Use `tool/run_dev.sh --lan` for physical device testing (rewrites endpoints to LAN IP)

### Vector Retrieval Pipeline
- Ingestion happens in `vectorial_db`, NOT `agents-service`
- GROBID extracts PDF metadata; PyMuPDF serves as fallback
- Dead Letter Queue (DLQ) for failed ingestions
- Use `scripts/ingest_test_papers.py` for seeding test data

### Flutter Development Helpers
- `tool/run_dev.sh` loads environment and handles device selection
- Add `tool/` to PATH: `export PATH="$PWD/tool:$PATH"`
- Then use: `flutter run dev` or `flutter run dev --lan`

### Multi-Service Testing
When testing cross-service flows:
1. Start vector DB: `cd services/vectordb && docker compose up -d`
2. Start agents service: `cd services/agents && uv run uvicorn main:app --reload --port 8080`
3. Start backend: `cd services/api && uv run python manage.py runserver`
4. Run mobile with LAN mode: `cd apps/mobile && flutter run dev --lan`
