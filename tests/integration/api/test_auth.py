"""Tests del endpoint de autenticación."""

import pytest


@pytest.mark.integration
def test_login_correcto_devuelve_token(client, admin_user):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "test_password_123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
def test_login_password_incorrecta_401(client, admin_user):
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_login_usuario_no_existe_401(client):
    response = client.post(
        "/api/auth/login",
        data={"username": "noexiste@test.com", "password": "any_password"},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_endpoint_protegido_sin_token_401(client):
    response = client.get("/api/bookings/")
    assert response.status_code == 401


@pytest.mark.integration
def test_login_rate_limit_429(client, admin_user, monkeypatch):
    """Superar el límite de intentos de login debe devolver 429.

    El rate limit está deshabilitado globalmente en tests (RATE_LIMIT_ENABLED=false
    en pytest.ini), así que lo habilitamos solo para esta prueba usando monkeypatch.
    """
    from app.config import settings as _settings
    monkeypatch.setattr(_settings, "RATE_LIMIT_ENABLED", True)

    # Los primeros 5 intentos son permitidos (aunque fallen con 401)
    for _ in range(5):
        client.post(
            "/api/auth/login",
            data={"username": "admin@test.com", "password": "wrong"},
        )

    # El 6.º intento debe ser bloqueado por rate limit
    response = client.post(
        "/api/auth/login",
        data={"username": "admin@test.com", "password": "wrong"},
    )
    assert response.status_code == 429


# ── Validación de schema ───────────────────────────────────────────────────────

@pytest.mark.integration
def test_login_campos_faltantes_422(client):
    """Login sin password debe devolver 422 (campo obligatorio faltante)."""
    response = client.post("/api/auth/login", data={"username": "admin@test.com"})
    assert response.status_code == 422


# ── Rutas protegidas: stats ────────────────────────────────────────────────────

@pytest.mark.integration
def test_stats_sin_token_401(client):
    """El endpoint /api/admin/stats sin token debe devolver 401."""
    response = client.get("/api/admin/stats")
    assert response.status_code == 401


@pytest.mark.integration
def test_stats_token_invalido_401(client):
    """El endpoint /api/admin/stats con token falso debe devolver 401."""
    response = client.get(
        "/api/admin/stats",
        headers={"Authorization": "Bearer token_inventado"},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_stats_con_token_valido_200(client, auth_headers):
    """El endpoint /api/admin/stats con JWT válido debe devolver 200."""
    response = client.get("/api/admin/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    for key in (
        "citas_hoy",
        "citas_semana",
        "citas_mes",
        "ingresos_estimados_semana",
        "ingresos_estimados_mes",
        "servicios_mas_solicitados",
        "distribucion_por_estado",
        "proxima_cita",
    ):
        assert key in data
