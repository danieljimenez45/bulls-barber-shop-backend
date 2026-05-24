# ──────────────────────────────────────────────────────────────────────────────
# backend/docker/Dockerfile — Bulls Barber Shop API
#
# Stages:
#   base  → imagen común (dependencias instaladas)
#   dev   → uvicorn con --reload, código montado como volumen en compose
#   prod  → imagen final sin privilegios, sin --reload
#
# Contexto de build: backend/   (un nivel arriba de docker/)
# ──────────────────────────────────────────────────────────────────────────────


# ══════════════════════════════════════════════════════════════════════════════
# BASE — dependencias comunes
# ══════════════════════════════════════════════════════════════════════════════
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalamos dependencias primero para aprovechar la caché de capas
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p uploads/gallery

EXPOSE 8000


# ══════════════════════════════════════════════════════════════════════════════
# DEV — hot reload, el código se monta como volumen desde el host
# ══════════════════════════════════════════════════════════════════════════════
FROM base AS dev

# En dev el código llega por volumen (no se copia en la imagen),
# por lo que los cambios se reflejan sin reconstruir.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--reload"]


# ══════════════════════════════════════════════════════════════════════════════
# PROD — imagen final sin privilegios, sin --reload
# ══════════════════════════════════════════════════════════════════════════════
FROM base AS prod

# Copiamos el código solo en producción (en dev viene por volumen)
COPY . .

# Usuario sin privilegios
RUN addgroup --system appgroup && \
    adduser  --system --ingroup appgroup appuser && \
    chown -R appuser:appgroup /app

USER appuser

# --workers 1: SQLite no admite escrituras concurrentes.
# Con PostgreSQL en producción puedes subir a 2-4 workers.
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--proxy-headers"]
