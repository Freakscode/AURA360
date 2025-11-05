FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ARG EXTRAS=""
COPY pyproject.toml .
COPY vectosvc vectosvc
COPY scripts scripts
RUN pip install -U pip setuptools wheel \
    && if [ -z "$EXTRAS" ]; then pip install -e .; else pip install -e .[$EXTRAS]; fi

COPY config config

EXPOSE 8000

CMD ["uvicorn", "vectosvc.api.http:app", "--host", "0.0.0.0", "--port", "8000"]
