"""Tests de integración de la API de reservas."""

from datetime import datetime

import pytest


FUTURE_SLOT = "2030-12-01T10:00:00"
FUTURE_SLOT_2 = "2030-12-01T11:00:00"


def _payload(**kwargs):
    defaults = {
        "nombre_cliente": "Pedro Martínez",
        "telefono": "611222333",
        "servicio_id": 1,
        "servicio_nombre": "Corte Clásico",
        "fecha_hora": FUTURE_SLOT,
    }
    defaults.update(kwargs)
    return defaults


# ── Endpoints públicos ─────────────────────────────────────────────────────────

@pytest.mark.integration
def test_crear_reserva_slot_libre_201(client, mocker):
    # Parchear el notifier para evitar envíos de email reales
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    response = client.post("/api/bookings/", json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["nombre_cliente"] == "Pedro Martínez"
    assert data["estado"] == "pendiente"


@pytest.mark.integration
def test_crear_reserva_slot_ocupado_409(client, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    # Crear la primera reserva
    client.post("/api/bookings/", json=_payload())
    # Intentar el mismo slot → 409
    response = client.post("/api/bookings/", json=_payload())
    assert response.status_code == 409


@pytest.mark.integration
def test_crear_reserva_campos_obligatorios_faltantes_422(client):
    response = client.post("/api/bookings/", json={"nombre_cliente": "Solo nombre"})
    assert response.status_code == 422


@pytest.mark.integration
def test_get_disponibilidad_200(client):
    response = client.get("/api/bookings/disponibilidad", params={"fecha": "2030-12-01"})
    assert response.status_code == 200
    data = response.json()
    assert "fecha" in data
    assert "slots_ocupados" in data


@pytest.mark.integration
def test_get_disponibilidad_fecha_invalida_422(client):
    response = client.get("/api/bookings/disponibilidad", params={"fecha": "no-es-fecha"})
    assert response.status_code == 422


# ── Endpoints protegidos ───────────────────────────────────────────────────────

@pytest.mark.integration
def test_listar_reservas_sin_token_401(client):
    response = client.get("/api/bookings/")
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_reservas_con_token_200(client, auth_headers):
    response = client.get("/api/bookings/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


@pytest.mark.integration
def test_listar_reservas_filtro_estado(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    client.post("/api/bookings/", json=_payload())
    response = client.get("/api/bookings/", headers=auth_headers, params={"estado": "pendiente"})
    assert response.status_code == 200
    data = response.json()
    assert all(b["estado"] == "pendiente" for b in data["items"])


@pytest.mark.integration
def test_get_reserva_por_id(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/bookings/", json=_payload()).json()
    booking_id = created["id"]
    response = client.get(f"/api/bookings/{booking_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == booking_id


@pytest.mark.integration
def test_get_reserva_no_existente_404(client, auth_headers):
    response = client.get("/api/bookings/99999", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.integration
def test_actualizar_estado_reserva(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/bookings/", json=_payload()).json()
    booking_id = created["id"]
    response = client.patch(
        f"/api/bookings/{booking_id}",
        headers=auth_headers,
        json={"estado": "confirmada"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "confirmada"


@pytest.mark.integration
def test_cancelar_reserva_204(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/bookings/", json=_payload()).json()
    booking_id = created["id"]
    response = client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.integration
def test_cancelar_reserva_ya_eliminada_404(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/bookings/", json=_payload()).json()
    booking_id = created["id"]
    client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    # Segundo delete → 404
    response = client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    assert response.status_code == 404
