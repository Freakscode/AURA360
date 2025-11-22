FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy shared messaging module first
COPY shared /app-shared
RUN pip install -e /app-shared

ARG EXTRAS=""
COPY vectordb/pyproject.toml .
COPY vectordb/vectosvc vectosvc
COPY vectordb/scripts scripts
RUN pip install -U pip setuptools wheel \
    && if [ -z "$EXTRAS" ]; then pip install -e .; else pip install -e .[$EXTRAS]; fi

COPY vectordb/config config

EXPOSE 8000

CMD ["uvicorn", "vectosvc.api.http:app", "--host", "0.0.0.0", "--port", "8000"]
