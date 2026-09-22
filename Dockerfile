# Imagem única do sistema: API FastAPI + frontend React já compilado.
# É a mesma imagem usada no docker-compose local e no deploy do Render.

# ---------- Etapa 1: build do frontend ----------
FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---------- Etapa 2: API servindo também o frontend ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UPLOAD_DIR=/app/uploads \
    STATIC_DIR=/app/static

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY --from=frontend /frontend/dist ./static

# Roda sem root; a pasta de uploads precisa ser gravável pelo usuário da app.
RUN useradd --create-home appuser \
    && mkdir -p /app/uploads \
    && chown -R appuser /app
USER appuser

EXPOSE 8000

# O Render informa a porta pela variável PORT; localmente usa 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
