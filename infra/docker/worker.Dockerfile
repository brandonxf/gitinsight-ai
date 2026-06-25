FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# git para clonado; build-essential para dependencias de análisis (tree-sitter, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY . .

# El comando concreto (worker / beat / flower) lo define docker-compose.
CMD ["celery", "-A", "app.workers.celery_app.celery", "worker", "--loglevel=INFO"]
