"""
Logging estructurado para Bulls Barber Shop API.

- DEBUG=True  → formato legible en consola (dev)
- DEBUG=False → formato JSON línea a línea (producción / ingesta en Loki, CloudWatch, etc.)
"""

import json
import logging
import sys
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


# ── Formateadores ─────────────────────────────────────────────────────────────

class _JSONFormatter(logging.Formatter):
    """Emite cada registro como un objeto JSON en una sola línea."""

    LEVEL_MAP = {
        logging.DEBUG:    "debug",
        logging.INFO:     "info",
        logging.WARNING:  "warning",
        logging.ERROR:    "error",
        logging.CRITICAL: "critical",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts":      self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":   self.LEVEL_MAP.get(record.levelno, record.levelname.lower()),
            "logger":  record.name,
            "msg":     record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Campos extra añadidos con logger.info("...", extra={...})
        for key, value in record.__dict__.items():
            if key not in {
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread",
                "threadName",
            }:
                payload[key] = value
        return json.dumps(payload, ensure_ascii=False, default=str)


_DEV_FORMAT = "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s"
_DEV_DATE   = "%H:%M:%S"


# ── Configuración global ──────────────────────────────────────────────────────

def setup_logging(debug: bool = True) -> None:
    """
    Configura el logging raíz de la aplicación.
    Llamar una sola vez al arrancar, antes de importar routers.
    """
    handler = logging.StreamHandler(sys.stdout)

    if debug:
        handler.setFormatter(logging.Formatter(_DEV_FORMAT, datefmt=_DEV_DATE))
        level = logging.DEBUG
    else:
        handler.setFormatter(_JSONFormatter())
        level = logging.INFO

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Silenciar librerías verbosas
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger con el nombre dado (convención: __name__ del módulo)."""
    return logging.getLogger(name)


# ── Middleware de peticiones HTTP ─────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Registra cada petición entrante con método, ruta, status y duración.
    Nivel INFO para respuestas normales, WARNING para 4xx, ERROR para 5xx.
    """

    _logger = get_logger("api.access")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 1)

        extra = {
            "method":      request.method,
            "path":        request.url.path,
            "status":      response.status_code,
            "duration_ms": duration_ms,
            "client":      request.client.host if request.client else "-",
        }

        msg = f"{request.method} {request.url.path} → {response.status_code} ({duration_ms} ms)"

        if response.status_code >= 500:
            self._logger.error(msg, extra=extra)
        elif response.status_code >= 400:
            self._logger.warning(msg, extra=extra)
        else:
            self._logger.info(msg, extra=extra)

        return response
