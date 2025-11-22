# Multi-stage Dockerfile for Django API (AURA360)
# Optimized for Railway deployment with production-ready configuration

FROM python:3.13-slim AS base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for PostgreSQL and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for faster dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy shared messaging module first (required dependency)
COPY services/shared /app/shared

# Copy dependency files
COPY services/api/pyproject.toml ./

# Replace absolute path with relative path for Docker build
RUN sed -i 's|file:///Users/freakscode/Proyectos%202025/AURA360/services/shared|file:///app/shared|g' pyproject.toml

# Install dependencies using uv
RUN uv pip install --system --no-cache .

# Copy application code
COPY services/api/ .

# Collect static files for production
RUN python manage.py collectstatic --noinput --clear

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health', timeout=5).raise_for_status()" || exit 1

# Expose port
EXPOSE 8000

# Run migrations and start gunicorn with multiple workers
# Railway will set PORT env var, but we default to 8000
CMD python manage.py migrate --noinput && \
    gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WEB_CONCURRENCY:-2} \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
