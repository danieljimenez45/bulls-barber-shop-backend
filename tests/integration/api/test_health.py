"""Tests del endpoint de health check."""

import pytest


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
