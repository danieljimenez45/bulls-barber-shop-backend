"""Tests de integración de la API de reservas."""

from datetime import datetime, timedelta, timezone

import pytest

from tests.helpers import FUTURE_SLOT, FUTURE_SLOT_2, booking_payload

pytestmark = pytest.mark.usefixtures("seed_booking_service")


# ── Endpoints públicos ─────────────────────────────────────────────────────────

@pytest.mark.integration
def test_crear_reserva_slot_libre_201(client, mocker):
    # Parchear el notifier para evitar envíos de email reales
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    response = client.post("/api/bookings/", json=booking_payload())
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
    client.post("/api/bookings/", json=booking_payload())
    # Intentar el mismo slot → 409
    response = client.post("/api/bookings/", json=booking_payload())
    assert response.status_code == 409


@pytest.mark.integration
def test_crear_reserva_fecha_pasada_422(client):
    pasado = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "")
    response = client.post(
        "/api/bookings/",
        json=booking_payload(fecha_hora=pasado),
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_crear_reserva_servicio_inactivo_400(client, auth_headers, mocker):
    mocker.patch("app.api.routers.bookings.SMTPBookingNotifier", return_value=mocker.Mock())
    created = client.post(
        "/api/services/",
        headers=auth_headers,
        json={
            "nombre": "Inactivo",
            "descripcion": "x",
            "precio": 10.0,
            "duracion_minutos": 30,
            "categoria": "corte",
            "activo": False,
            "orden": 0,
        },
    ).json()
    response = client.post(
        "/api/bookings/",
        json=booking_payload(servicio_id=created["id"]),
    )
    assert response.status_code == 400


@pytest.mark.integration
def test_crear_reserva_servicio_nombre_proviene_de_bd(client, mocker):
    """El servicio_nombre en la respuesta siempre viene de BD, no del payload."""
    mocker.patch("app.api.routers.bookings.SMTPBookingNotifier", return_value=mocker.Mock())
    response = client.post("/api/bookings/", json=booking_payload())
    assert response.status_code == 201
    assert response.json()["servicio_nombre"] == "Corte Clásico"


@pytest.mark.integration
def test_patch_cancelada_rechazado_422(client, auth_headers, mocker):
    """PATCH con estado=cancelada devuelve 422: Pydantic rechaza el valor en
    el schema (cancelada no está en el Literal de BookingUpdate.estado).
    La cancelación solo se permite a través de DELETE /api/bookings/{id}."""
    mocker.patch("app.api.routers.bookings.SMTPBookingNotifier", return_value=mocker.Mock())
    created = client.post("/api/bookings/", json=booking_payload()).json()
    response = client.patch(
        f"/api/bookings/{created['id']}",
        headers=auth_headers,
        json={"estado": "cancelada"},
    )
    assert response.status_code == 422


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


@pytest.mark.integration
def test_get_disponibilidad_sin_reservas_slots_vacios(client):
    response = client.get("/api/bookings/disponibilidad", params={"fecha": "2035-01-01"})
    assert response.status_code == 200
    assert response.json()["slots_ocupados"] == []


@pytest.mark.integration
def test_dos_slots_distintos_se_pueden_reservar(client, mocker):
    mocker.patch("app.api.routers.bookings.SMTPBookingNotifier", return_value=mocker.Mock())
    r1 = client.post("/api/bookings/", json=booking_payload(fecha_hora="2030-12-01T10:00:00"))
    r2 = client.post("/api/bookings/", json=booking_payload(fecha_hora="2030-12-01T11:00:00"))
    assert r1.status_code == 201
    assert r2.status_code == 201


@pytest.mark.integration
def test_slot_ocupado_aparece_en_disponibilidad(client, mocker):
    mocker.patch("app.api.routers.bookings.SMTPBookingNotifier", return_value=mocker.Mock())
    client.post("/api/bookings/", json=booking_payload(fecha_hora="2030-12-02T10:00:00"))
    response = client.get("/api/bookings/disponibilidad", params={"fecha": "2030-12-02"})
    assert len(response.json()["slots_ocupados"]) == 1


@pytest.mark.integration
def test_listar_reservas_paginacion_size(client, auth_headers, mocker):
    mocker.patch("app.api.routers.bookings.SMTPBookingNotifier", return_value=mocker.Mock())
    for i in range(3):
        client.post("/api/bookings/", json=booking_payload(fecha_hora=f"2030-12-0{i + 3}T10:00:00"))
    response = client.get("/api/bookings/?page=1&size=2", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2
    assert data["size"] == 2


# ── Validaciones de schema ─────────────────────────────────────────────────────

@pytest.mark.integration
def test_crear_reserva_nombre_demasiado_largo_422(client):
    """nombre_cliente con más de 100 caracteres debe devolver 422."""
    response = client.post("/api/bookings/", json=booking_payload(nombre_cliente="A" * 101))
    assert response.status_code == 422


@pytest.mark.integration
def test_crear_reserva_telefono_demasiado_largo_422(client):
    """Teléfono con más de 20 caracteres debe devolver 422."""
    response = client.post("/api/bookings/", json=booking_payload(telefono="1" * 21))
    assert response.status_code == 422


@pytest.mark.integration
def test_crear_reserva_email_invalido_422(client):
    """Email con formato incorrecto debe devolver 422."""
    response = client.post("/api/bookings/", json=booking_payload(email="no-es-un-email"))
    assert response.status_code == 422


@pytest.mark.integration
def test_actualizar_estado_invalido_422(client, auth_headers, mocker):
    """Estado fuera de los valores permitidos debe devolver 422."""
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/bookings/", json=booking_payload()).json()
    response = client.patch(
        f"/api/bookings/{created['id']}",
        headers=auth_headers,
        json={"estado": "inventado"},
    )
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
    client.post("/api/bookings/", json=booking_payload())
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
    created = client.post("/api/bookings/", json=booking_payload()).json()
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
    created = client.post("/api/bookings/", json=booking_payload()).json()
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
    created = client.post("/api/bookings/", json=booking_payload()).json()
    booking_id = created["id"]
    response = client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    assert response.status_code == 204


@pytest.mark.integration
def test_cancelar_reserva_ya_eliminada_404(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/bookings/", json=booking_payload()).json()
    booking_id = created["id"]
    client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    # Segundo delete → 404
    response = client.delete(f"/api/bookings/{booking_id}", headers=auth_headers)
    assert response.status_code == 404
