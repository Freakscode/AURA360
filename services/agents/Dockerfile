# Dockerfile for Agents Service (AURA360)
# FastAPI + Google ADK + Vector Retrieval
# Optimized for Railway deployment

FROM python:3.11-slim AS base

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies
RUN uv pip install --system --no-cache .

# Copy application code
COPY . .

# Health check - /readyz endpoint already exists in main.py
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8080/readyz', timeout=5).raise_for_status()" || exit 1

# Expose port
EXPOSE 8080

# Start uvicorn with multiple workers
CMD uvicorn main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8080} \
    --workers ${WEB_CONCURRENCY:-2} \
    --log-level info \
    --access-log \
    --use-colors
