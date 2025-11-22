# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

AURA360 is a holistic wellness platform monorepo that integrates mind, body, and soul tracking with AI-powered guidance. The project uses an event-driven microservices architecture with Kafka for inter-service communication.

**Key Technologies:**
- **Mobile:** Flutter 3.24+ with Riverpod for state management, Supabase for auth/database
- **Web:** Angular 20 with Material Design
- **Backend API:** Django 5.2 with Django REST Framework, PostgreSQL via Supabase
- **Agents:** Google ADK (Agent Development Kit) with FastAPI, Qdrant vector database
- **Vector DB:** FastAPI + Celery + Qdrant + Redis for biomedical document search and RAG
- **Messaging:** Kafka (Confluent Cloud) for event-driven communication
- **Infrastructure:** Docker Compose for local development, Azure/GCP for production

## Development Commands

### Mobile App (Flutter)
```bash
cd apps/mobile
flutter pub get
export PATH="$PWD/tool:$PATH"  # Adds custom run_dev.sh to PATH

# Run in development mode (uses env/local.env)
flutter run dev
# Or use the custom wrapper for interactive device selection:
run_dev.sh

# Run with LAN IP for physical device testing
run_dev.sh --lan

# Run tests
flutter test --coverage
flutter analyze
dart format .
```

**Mobile-specific notes:**
- Environment variables are loaded from `apps/mobile/env/local.env` (copy from `local.env.example`)
- The `tool/run_dev.sh` script handles device selection, LAN IP detection, and environment loading
- Tests mirror the source structure: `lib/features/X/file.dart` → `test/features/X/file_test.dart`

### Web Frontend (Angular)
```bash
cd apps/web
npm install
ng serve                 # Starts dev server on http://localhost:4200
ng test                  # Runs Jasmine/Karma tests
ng build                 # Production build
ng lint                  # Runs linting
```

### Django API
```bash
cd services/api
uv sync                                      # Install dependencies
uv run python manage.py runserver 0.0.0.0:8000
uv run python manage.py test                # Run Django tests
uv run python manage.py makemigrations      # Create migrations
uv run python manage.py migrate             # Apply migrations

# Using pytest (if available)
uv run pytest tests/
```

**API-specific notes:**
- Environment variables in `services/api/.env` (copy from `.env.example`)
- Uses Supabase for authentication and PostgreSQL database
- Django apps: `users`, `holistic`, `body` (see `pyproject.toml` packages)

### Agents Service (Google ADK)
```bash
cd services/agents
uv sync
uv run uvicorn main:app --reload --port 8080  # Start FastAPI server
uv run pytest                                  # Run all tests
uv run pytest tests/unit/                     # Run unit tests only
uv run pytest tests/integration/              # Run integration tests only

# Testing specific components
uv run pytest tests/unit/test_topic_classifier.py -v
```

**Agents-specific notes:**
- Environment loaded via `infra/env.py` from `services/agents/.env`
- Agents orchestrate AI using Google ADK and query Qdrant for RAG
- Main routers in `agents_service/api/routers/`
- Agent implementations in `holistic_agent/` and `nutritional_agent/`
- Kafka integration in `kafka/` directory for event-driven communication

### Vector Database Service
```bash
cd services/vectordb

# Start all services (Qdrant, Redis, GROBID, API, worker, Kafka consumer)
docker compose up -d

# View logs
docker compose logs -f api
docker compose logs -f worker

# Run tests
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v --cov=vectosvc

# Stop services
docker compose down
```

**VectorDB-specific notes:**
- Uses Qdrant for vector storage, Redis for Celery task queue, GROBID for PDF parsing
- Exposes REST API on port 8001 (mapped from container port 8000)
- Celery worker processes document embedding tasks asynchronously
- Kafka consumer listens for events from other services
- Environment variables in `.env` or via docker-compose.yml
- Collection name controlled by `VECTOR_COLLECTION_NAME` env var (default: `holistic_memory`)

### Shared Messaging Library
```bash
cd services/shared
# This is a Python package, not a service
# Used by api, agents, and vectordb for Kafka event communication
```

**Messaging notes:**
- Provides common Kafka producers/consumers and event schemas
- Used via dependency: `aura360-messaging @ file:///.../services/shared`
- See `services/shared/README.md` for event schemas

## Common Development Workflows

### Running Full Stack Locally

1. **Start Vector DB services:**
   ```bash
   cd services/vectordb
   docker compose up -d
   ```

2. **Start Django API:**
   ```bash
   cd services/api
   uv run python manage.py runserver 0.0.0.0:8000
   ```

3. **Start Agents service:**
   ```bash
   cd services/agents
   uv run uvicorn main:app --reload --port 8080
   ```

4. **Start Web or Mobile:**
   ```bash
   # Web
   cd apps/web && ng serve

   # Mobile
   cd apps/mobile && run_dev.sh
   ```

### Running Tests Before Commits

```bash
# Mobile
cd apps/mobile && flutter test && flutter analyze

# Web
cd apps/web && ng test --watch=false

# API
cd services/api && uv run python manage.py test

# Agents
cd services/agents && uv run pytest

# VectorDB
cd services/vectordb && pytest tests/ -v
```

### Working with Qdrant Vector Database

The vector database is accessed in two ways:
1. **Local Docker:** `http://localhost:6333` (when running `docker compose up` in `services/vectordb`)
2. **Qdrant Cloud:** Configured via `QDRANT_URL` and `QDRANT_API_KEY` environment variables

**Common Qdrant operations:**
```bash
cd services/agents

# Test Qdrant connection
uv run python test_qdrant_connection.py

# Test semantic search
uv run python test_semantic_search.py

# Verify integration with GCP credentials
cd ../../scripts
./verify_qdrant_integration.sh
```

### Working with GCP and Credentials

```bash
# Setup GCP authentication (Application Default Credentials)
./scripts/setup_gcp_auth.sh

# The script configures:
# - gcloud auth application-default login
# - Sets GCP_PROJECT, GCP_REGION
# - Creates credentials at ~/.config/gcloud/application_default_credentials.json

# For vector DB, mount credentials in docker-compose:
# volumes:
#   - ${HOME}/.config/gcloud/application_default_credentials.json:/tmp/adc.json:ro
```

## Architecture Key Points

### Service Communication

**Event-Driven (Kafka):**
- Services communicate asynchronously via Kafka topics
- Event schemas defined in `services/shared/messaging/`
- Confluent Cloud used in production, local Kafka for development
- Key topics: wellness intake events, user context updates, nutrition plans

**Synchronous (HTTP):**
- Mobile/Web → Django API for user management, CRUD operations
- Agents → Vector DB service for semantic search
- All services expose health checks at `/readyz`

### Authentication Flow

1. Mobile/Web authenticates with Supabase (JWT tokens)
2. Supabase JWT validated by Django API
3. Django API creates/updates user records
4. User context propagated to agents via Kafka events
5. Agents use context for personalized recommendations

### Data Flow for AI Recommendations

1. **User action** (e.g., logs mood/meal) → **Mobile/Web**
2. **Mobile/Web** → **Django API** (REST)
3. **Django API** → **Kafka** (user context event)
4. **Kafka** → **Agents Service** (consumes event)
5. **Agents** → **Vector DB** (semantic search for biomedical knowledge)
6. **Agents** → **Google ADK** (generates holistic recommendation)
7. **Agents** → **Mobile/Web** (returns advice)

### Directory Structure Highlights

```
AURA360/
├── apps/
│   ├── mobile/          # Flutter: lib/ (source), test/ (tests), env/ (configs)
│   └── web/             # Angular: src/app/ (features), *.spec.ts (tests)
├── services/
│   ├── api/             # Django: config/ (settings), users/, holistic/, body/ (apps)
│   ├── agents/          # FastAPI: agents_service/, holistic_agent/, nutritional_agent/
│   ├── vectordb/        # FastAPI: vectosvc/ (api/, worker/, kafka/)
│   ├── pdf-extraction/  # PDF parsing service
│   └── shared/          # messaging/ (Kafka event library)
├── docs/
│   └── runbooks/        # Operational guides for deployment, Kafka, setup
├── scripts/             # Deployment, testing, and utility scripts
└── infra/               # Infrastructure as code (azure/, gcp/)
```

## Testing Guidelines

### Test Organization

- **Mobile:** `test/` mirrors `lib/` structure
- **Web:** `*.spec.ts` files alongside source components
- **Backend services:** `tests/unit/` and `tests/integration/` directories

### Test Naming Conventions

- Flutter: `test_description_of_behavior` in `describe()` blocks
- Python: `test_function_name_behavior` (pytest style)
- Angular: `should do something` (Jasmine style)

### Mocking External Services

- **Qdrant:** Mock with in-memory client or use test collection
- **Supabase:** Use responses library or mock HTTP calls
- **Kafka:** Mock producers/consumers with in-memory queues
- **Google ADK:** Mock model responses with fixed outputs

## Environment Variables

### Critical Variables per Service

**Mobile (`apps/mobile/env/local.env`):**
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DATABASE`
- `BASE_URL` (points to Django API)

**API (`services/api/.env`):**
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
- `SECRET_KEY`, `DATABASE_URL`
- Kafka settings: `KAFKA_BOOTSTRAP_SERVERS`

**Agents (`services/agents/.env`):**
- `GOOGLE_API_KEY` (for ADK/Gemini)
- `QDRANT_URL`, `QDRANT_API_KEY`
- `VECTOR_SERVICE_URL` (points to vectordb service)
- Kafka settings

**VectorDB (`services/vectordb/.env` or docker-compose.yml):**
- `QDRANT_URL`, `QDRANT_GRPC`
- `BROKER_URL`, `RESULT_BACKEND` (Redis for Celery)
- `VECTOR_COLLECTION_NAME`
- `GOOGLE_APPLICATION_CREDENTIALS`, `GCS_PROJECT`

## Commit Conventions

Follow **Conventional Commits** with service scope:

```
<type>(<scope>): <description>

[optional body]
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`

**Scopes:** `mobile`, `web`, `api`, `agents`, `vectordb`, `pdf`, `shared`, `docs`, `infra`, `core`

**Examples:**
- `feat(agents): add topic classification for holistic queries`
- `fix(api): validate Supabase JWT expiration`
- `docs(vectordb): update Qdrant integration guide`
- `chore(mobile): upgrade Flutter to 3.24.5`

## Troubleshooting Common Issues

### Flutter: "Missing env file"
- Ensure `apps/mobile/env/local.env` exists (copy from `local.env.example`)
- Check `export PATH="$PWD/tool:$PATH"` is set before running `flutter run dev`

### Django: "No module named 'aura360_messaging'"
- Install shared package: `cd services/shared && uv pip install -e .`
- Or run `uv sync` in services/api (should install from local path)

### Agents: "Cannot connect to Qdrant"
- Check `QDRANT_URL` in `.env` points to correct endpoint
- For local: ensure `cd services/vectordb && docker compose up -d` is running
- For cloud: verify `QDRANT_API_KEY` is set

### VectorDB: "Permission denied" on mounted credentials
- Run `./scripts/setup_gcp_auth.sh` to create ADC credentials
- Ensure `~/.config/gcloud/application_default_credentials.json` exists
- Check docker-compose.yml volume mount is correct

### Kafka connection errors
- Verify `KAFKA_BOOTSTRAP_SERVERS` points to correct Confluent Cloud cluster
- Check Kafka API credentials in `.env`
- For local development, ensure Kafka container is running

## Deployment

Deployment procedures are documented in `docs/runbooks/deployment/`. Key scripts:

- `scripts/deploy_api_gcloud.sh` - Deploy Django API to GCP Cloud Run
- `scripts/deploy_web_gcloud.sh` - Deploy Angular web to GCP
- `scripts/deploy_worker_gcloud.sh` - Deploy Celery worker to GCP
- `.github/workflows/deploy-azure.yml` - Azure deployment pipeline

Before deploying:
1. Review `docs/runbooks/deployment/DEPLOYMENT_CHECKLIST.md`
2. Set up production credentials: `scripts/setup_env_production.sh`
3. Test locally with production-like config

## Additional Resources

- **Architecture docs:** `docs/architecture/`
- **Kafka setup:** `docs/runbooks/kafka/`
- **Testing guides:** `docs/testing/`
- **Supabase setup:** `docs/runbooks/setup/SUPABASE_SETUP.md`
- **Agent routing logic:** `services/agents/GUARDIAN_ROUTING.md`
- **Kafka request-reply:** `services/agents/GUARDIAN_KAFKA_REQUEST_REPLY.md`

## Language Preferences

- Recuerda siempre responder en español
- No debes generar documentación a no ser que se te solicite explícitamente