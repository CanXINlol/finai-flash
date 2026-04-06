# ── Stage 1: Frontend build ──────────────────────────────
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Python runtime ──────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# App source
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Frontend static files
COPY --from=frontend-builder /frontend/dist ./static/

# Data directory
RUN mkdir -p /app/data

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
