"""
health.py
─────────────────────────────────────────────────────────────────────────────
Endpoint de health check para monitorización y readiness probes.

GET /api/health
  • Comprueba la conectividad con la base de datos (SELECT 1)
  • Devuelve 200 si todo está bien, 503 si la BD no responde
  • Incluye timestamp UTC y versión de la API para facilitar el diagnóstico
─────────────────────────────────────────────────────────────────────────────
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter()

# Versión de la API — actualizar al hacer releases
API_VERSION = "1.0.0"


@router.get(
    "/",
    summary="Health check",
    tags=["Health"],
    response_description="Estado del servicio y de la base de datos",
)
def health_check(db: Session = Depends(get_db)):
    """
    Comprueba el estado general de la API.

    - **status**: `ok` si todo funciona, `degraded` si la BD no responde.
    - **db**: `ok` | `error`.
    - **timestamp**: instante UTC de la comprobación.
    - **version**: versión de la API.

    Devuelve HTTP 503 cuando la base de datos no es accesible.
    """
    db_status = "ok"
    db_error: str | None = None

    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        db_status = "error"
        db_error = str(exc)

    overall = "ok" if db_status == "ok" else "degraded"
    http_status = 200 if overall == "ok" else 503

    payload: dict = {
        "status":    overall,
        "db":        db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version":   API_VERSION,
    }
    if db_error:
        payload["db_error"] = db_error

    return JSONResponse(content=payload, status_code=http_status)
