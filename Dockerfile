FROM node:20-slim AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json ./package.json
RUN npm install

COPY frontend/ ./
RUN npm run build


FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/
COPY alembic.ini ./alembic.ini
COPY pyproject.toml ./pyproject.toml
COPY .env.example ./.env.example
COPY README.md ./README.md

COPY --from=frontend-builder /frontend/dist ./static/

RUN mkdir -p /app/data

EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]
