# GEMINI Context File: AURA360

This file provides context for the Gemini agent working on the AURA360 project.

## 1. Project Overview
**AURA360** is a comprehensive wellness platform integrating mind, body, and soul tracking with AI-powered holistic guidance.
It is a **monorepo** that includes mobile and web clients, backend services, and AI agents.

## 2. Architecture & Structure

### Directory Map
*   `apps/` - Client applications
    *   `mobile/` - Flutter mobile application (iOS/Android).
    *   `web/` - Angular web application (Platform administration/User portal).
*   `services/` - Backend services
    *   `api/` - Main Django REST API (User management, core business logic).
    *   `agents/` - AI Agents service (Google ADK, FastAPI, RAG).
    *   `vectordb/` - Vector database service (Qdrant, FastAPI, Celery).
    *   `pdf-extraction/` - Service for processing PDF documents.
*   `docs/` - Documentation (Architecture, Quality Plans, Runbooks).
*   `scripts/` - Utility scripts for deployment, testing, and setup.
*   `infra/` - Infrastructure configuration (Azure, Helm, Terraform).

### Technology Stack
*   **Frontend Mobile:** Flutter 3.24+ (Riverpod, Supabase).
*   **Frontend Web:** Angular 20.3+ (TypeScript, Supabase).
*   **Backend API:** Python 3.11+, Django 5.1, Django REST Framework.
*   **AI/ML:** Google Agent Development Kit (ADK), RAG Pipeline, Qdrant Vector DB.
*   **Database:** Supabase (PostgreSQL), Qdrant.
*   **Package Managers:** `uv` (Python), `npm` (Node.js), `pub` (Dart).

## 3. Development Workflow

### Prerequisites
*   Python 3.11+ (managed with `uv`)
*   Node.js 20+
*   Flutter 3.24+
*   Docker & Docker Compose

### Setup & Installation
*   **Python Services:** Use `uv sync` in respective service directories.
*   **Web:** `npm install` in `apps/web`.
*   **Mobile:** `flutter pub get` in `apps/mobile`.
*   **Environment:** Copy `.env.example` to `.env` in each service/app directory.

### Running Services
*   **Infrastructure (Vector DB, etc.):**
    ```bash
    cd services/vectordb && docker compose up -d
    ```
*   **Django API:**
    ```bash
    cd services/api && uv run python manage.py runserver 0.0.0.0:8000
    ```
*   **Agents Service:**
    ```bash
    cd services/agents && uv run uvicorn main:app --reload --port 8080
    ```
*   **Mobile App:**
    ```bash
    cd apps/mobile && flutter run
    ```
*   **Web App:**
    ```bash
    cd apps/web && ng serve
    ```

### Testing
*   **Integration Tests:** `./scripts/run_integration_tests.sh`
*   **E2E User Context:** `./scripts/run_user_context_e2e.sh`
*   **Mobile:** `flutter test` (in `apps/mobile`)
*   **API:** `uv run python manage.py test` (in `services/api`)
*   **Web:** `ng test` (in `apps/web`)

## 4. Coding Conventions

### Python (Backend/Agents)
*   **Style:** Follow PEP 8.
*   **Formatting:** Use `black` and `ruff`.
*   **Typing:** Strong typing with type hints is required for public APIs.
*   **Docstrings:** Required for all public functions/classes.

### Dart (Flutter)
*   **Style:** Follow "Effective Dart".
*   **Formatting:** Run `dart format .`
*   **Analysis:** Must pass `flutter analyze`.
*   **Naming:** `snake_case` for files, `PascalCase` for classes, `camelCase` for variables.

### TypeScript (Angular)
*   **Style:** Angular Style Guide.
*   **Linting:** `ng lint`.

### Git Commit Messages
Follow **Conventional Commits**:
*   `feat(scope): description`
*   `fix(scope): description`
*   Scopes: `mobile`, `web`, `api`, `agents`, `vectordb`, `docs`.

## 5. Key utility scripts (in `/scripts`)
*   `deploy_*.sh` - Scripts for deploying various components to GCloud.
*   `verify_deployments.sh` - Verifies that deployments are healthy.
*   `run_celery.sh` - Starts Celery workers.
