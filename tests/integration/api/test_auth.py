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
