"""Tests unitarios del servicio JWT (infraestructura de seguridad)."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.domain.auth.ports import TokenInvalid
from app.infrastructure.security.jwt_service import JWTService


# Clave y algoritmo fijos para los tests — independientes de settings
_SECRET = "test-secret-key-para-pruebas-unitarias"
_ALGORITHM = "HS256"


def _service() -> JWTService:
    """Instancia de JWTService que usa la SECRET_KEY cargada desde pytest.ini / .env.test."""
    return JWTService()


# ── create_token ──────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_create_token_devuelve_string_no_vacio():
    """create_token debe devolver un string JWT no vacío."""
    svc = _service()
    token = svc.create_token({"sub": "42"})
    assert isinstance(token, str)
    assert len(token) > 20


@pytest.mark.unit
def test_create_token_incluye_subject_en_payload():
    """El payload del token debe incluir el campo 'sub' original."""
    svc = _service()
    token = svc.create_token({"sub": "99"})
    # Decodificamos sin verificar expiración para inspeccionar el payload
    from app.config import settings
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "99"


@pytest.mark.unit
def test_create_token_incluye_exp():
    """El token generado debe incluir el campo de expiración 'exp'."""
    svc = _service()
    token = svc.create_token({"sub": "1"})
    from app.config import settings
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert "exp" in payload


# ── decode_token ──────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_decode_token_devuelve_payload_correcto():
    """decode_token debe devolver el payload completo del token."""
    svc = _service()
    token = svc.create_token({"sub": "7", "role": "admin"})
    payload = svc.decode_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "admin"


@pytest.mark.unit
def test_decode_token_invalido_lanza_token_invalid():
    """Un token con firma incorrecta debe lanzar TokenInvalid."""
    svc = _service()
    token_falso = "este.no.es.un.jwt.valido"
    with pytest.raises(TokenInvalid):
        svc.decode_token(token_falso)


@pytest.mark.unit
def test_decode_token_expirado_lanza_token_invalid():
    """Un token ya expirado debe lanzar TokenInvalid."""
    from app.config import settings

    # Creamos un token con expiración en el pasado directamente con jwt
    expired_token = jwt.encode(
        {
            "sub": "5",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    svc = _service()
    with pytest.raises(TokenInvalid):
        svc.decode_token(expired_token)
