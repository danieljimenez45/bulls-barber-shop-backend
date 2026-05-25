"""Tests del endpoint de health check."""

import pytest
from unittest.mock import patch
from sqlalchemy.exc import OperationalError


@pytest.mark.integration
def test_health_check_200(client):
    response = client.get("/api/health/")
    assert response.status_code == 200


@pytest.mark.integration
def test_health_check_estructura_respuesta(client):
    response = client.get("/api/health/")
    data = response.json()
    assert "status" in data
    assert "db" in data
    assert "timestamp" in data
    assert "version" in data
    assert data["status"] == "ok"
    assert data["db"] == "ok"


# ── Exposición controlada de errores según entorno ─────────────────────────────

@pytest.mark.integration
def test_health_no_expone_detalle_error_en_produccion(client, monkeypatch):
    """En producción (DEBUG=False) el detalle del error de BD no debe aparecer en la respuesta."""
    from app.config import settings as _settings
    monkeypatch.setattr(_settings, "DEBUG", False)

    with patch("sqlalchemy.orm.Session.execute", side_effect=OperationalError("fallo", {}, None)):
        response = client.get("/api/health/")

    assert response.status_code == 503
    data = response.json()
    assert data["db"] == "error"
    assert "db_error" not in data, "El detalle del error no debe exponerse en producción"


@pytest.mark.integration
def test_health_expone_detalle_error_en_desarrollo(client, monkeypatch):
    """En desarrollo (DEBUG=True) el detalle del error sí debe incluirse para diagnóstico."""
    from app.config import settings as _settings
    monkeypatch.setattr(_settings, "DEBUG", True)

    with patch("sqlalchemy.orm.Session.execute", side_effect=OperationalError("fallo_debug", {}, None)):
        response = client.get("/api/health/")

    assert response.status_code == 503
    data = response.json()
    assert "db_error" in data, "El detalle del error debe incluirse cuando DEBUG=True"
