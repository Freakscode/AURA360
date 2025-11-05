# AURA360 - Holistic Wellness Platform

A comprehensive wellness platform that integrates mind, body, and soul tracking with AI-powered holistic guidance.

## Architecture

This is a **monorepo** containing:

### 🎯 Client Applications (`/apps`)
- **mobile** - Flutter mobile app with mind/body/soul modules
- **web** - Angular 20 web frontend

### ⚙️ Backend Services (`/services`)
- **api** - Django REST API for user management (Supabase-backed)
- **agents** - Google ADK-based holistic AI agents with RAG
- **vectordb** - FastAPI + Celery + Qdrant for biomedical document search
- **pdf-extraction** - PDF processing service

### 📚 Documentation (`/docs`)
- Architecture documentation
- Testing guides and reports
- Module implementation details
- API documentation

## Quick Start

### Prerequisites
- **Python 3.11+** with [uv](https://github.com/astral-sh/uv) package manager
- **Flutter 3.24+**
- **Node.js 20+** and npm
- **Docker** and Docker Compose
- **Supabase** account (for authentication and database)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AURA360
   ```

2. **Set up environment variables**
   ```bash
   # Copy example files and fill in your credentials
   cp apps/mobile/env/local.env.example apps/mobile/env/local.env
   cp services/api/.env.example services/api/.env
   cp services/agents/.env.example services/agents/.env
   cp services/vectordb/.env.example services/vectordb/.env
   ```

3. **Start backend services**
   ```bash
   # Start vector database and dependencies
   cd services/vectordb
   docker compose up -d

   # Start Django API
   cd ../api
   uv sync
   uv run python manage.py runserver 0.0.0.0:8000

   # Start agents service
   cd ../agents
   uv sync
   uv run uvicorn main:app --reload --port 8080
   ```

4. **Run mobile app**
   ```bash
   cd apps/mobile
   flutter pub get
   export PATH="$PWD/tool:$PATH"
   flutter run dev
   ```

5. **Run web frontend**
   ```bash
   cd apps/web
   npm install
   ng serve
   ```

## Development Workflow

### Running Tests

```bash
# Mobile tests
cd apps/mobile
flutter test --coverage

# Backend tests
cd services/api
uv run python manage.py test

# Vector DB tests
cd services/vectordb
pytest tests/ -v --cov=vectosvc

# Agents tests
cd services/agents
uv run pytest

# Web tests
cd apps/web
ng test
```

### Code Quality

```bash
# Flutter analysis
cd apps/mobile
flutter analyze
dart format .

# Python formatting (if using black/ruff)
cd services/api
uv run black .
uv run ruff check .
```

## Project Structure

```
AURA360/
├── apps/
│   ├── mobile/          # Flutter mobile client
│   └── web/             # Angular web frontend
├── services/
│   ├── api/             # Django REST API
│   ├── agents/          # AI agents service
│   ├── vectordb/        # Vector database service
│   └── pdf-extraction/  # PDF processing
├── docs/                # Documentation
├── scripts/             # Shared scripts
├── .github/             # CI/CD workflows
└── CLAUDE.md            # AI development guide
```

## Key Features

### Mind Module
- Mood tracking with tags and notes
- Emotional pattern analysis
- Psychosocial context management

### Body Module
- Physical activity tracking
- Nutrition plans and meal logging
- Sleep monitoring

### Soul Module
- IKIGAI profile management
- Purpose and values alignment
- Holistic wellness integration

### AI Agents
- Context-aware holistic advice
- Nutritional recommendations
- Vector-based biomedical knowledge retrieval

## Technology Stack

- **Mobile**: Flutter 3.24+, Riverpod, Supabase
- **Web**: Angular 20, TypeScript
- **Backend**: Django 5.1, Django REST Framework
- **Agents**: Google ADK, FastAPI, Qdrant
- **Database**: Supabase (PostgreSQL), Qdrant (Vector DB)
- **Infrastructure**: Docker, Docker Compose

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development guidelines and commit conventions.

## Documentation

- [Architecture Overview](./docs/architecture/)
- [Testing Guide](./docs/testing/)
- [Module Documentation](./docs/modules/)
- [API Documentation](./docs/api/)

## License

[Add your license here]

## Support

For issues and questions, please use the GitHub issue tracker.
