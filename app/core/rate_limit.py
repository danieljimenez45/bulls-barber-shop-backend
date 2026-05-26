"""
Rate limiting in-memory con ventana deslizante.

Sin dependencias externas — adecuado para instancia única (un proceso Uvicorn).
Para despliegues multi-proceso o multi-instancia, sustituir por Redis + lua script.

Uso:
    from app.core.rate_limit import limiter

    @router.post("/")
    def crear(
        _: None = Depends(limiter(max_requests=10, window_seconds=60)),
        ...
    ):
        ...
"""

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Depends, HTTPException, Request, status

from app.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Almacén global: (ip, endpoint) → deque de timestamps
_store: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)


def _get_client_ip(request: Request) -> str:
    """Extrae la IP del cliente; X-Forwarded-For solo si TRUST_PROXY_HEADERS está activo."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def limiter(max_requests: int, window_seconds: int = 60):
    """
    Factoria de dependencias FastAPI.

    Args:
        max_requests:    Número máximo de peticiones permitidas en la ventana.
        window_seconds:  Tamaño de la ventana en segundos (defecto: 60).

    Returns:
        Función async compatible con Depends().

    Raises:
        HTTP 429 si se supera el límite.
        HTTP 503 si ocurre un error interno (nunca bloquea la petición original).
    """

    async def _check(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        ip = _get_client_ip(request)
        key = (ip, request.url.path)
        now = time.monotonic()
        cutoff = now - window_seconds

        bucket = _store[key]

        # Eliminar timestamps fuera de la ventana
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= max_requests:
            retry_after = int(window_seconds - (now - bucket[0])) + 1
            logger.warning(
                "Rate limit superado",
                extra={
                    "ip": ip,
                    "path": request.url.path,
                    "limit": max_requests,
                    "window_s": window_seconds,
                    "retry_after": retry_after,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Demasiadas peticiones. Máximo {max_requests} "
                    f"por {window_seconds} segundos. "
                    f"Inténtalo en {retry_after} segundos."
                ),
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)

    return _check
