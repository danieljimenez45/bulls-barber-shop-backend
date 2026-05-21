"""Tests de integración para el endpoint /api/bookings."""

from datetime import datetime, timedelta


def _future_datetime(days=7, hour=10) -> str:
    dt = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
    dt += timedelta(days=days)
    return dt.isoformat()


def _booking_payload(**kwargs) -> dict:
    base = {
        "nombre_cliente": "Juan Pérez",
        "telefono": "600000001",
        "servicio_id": 1,
        "servicio_nombre": "Corte",
        "fecha_hora": _future_datetime(),
    }
    base.update(kwargs)
    return base


# ── GET /api/bookings/disponibilidad ─────────────────────────────────────────

class TestDisponibilidad:
    def test_devuelve_slots_vacios(self, client):
        resp = client.get("/api/bookings/disponibilidad", params={"fecha": "2026-07-01"})
        assert resp.status_code == 200
        data = resp.json()
        assert "slots_ocupados" in data
        assert data["slots_ocupados"] == []

    def test_sin_fecha_devuelve_422(self, client):
        resp = client.get("/api/bookings/disponibilidad")
        assert resp.status_code == 422

    def test_fecha_invalida_devuelve_422(self, client):
        resp = client.get("/api/bookings/disponibilidad", params={"fecha": "no-es-fecha"})
        assert resp.status_code == 422


# ── POST /api/bookings ────────────────────────────────────────────────────────

class TestCrearReserva:
    def test_crea_reserva_correctamente(self, client):
        resp = client.post("/api/bookings/", json=_booking_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre_cliente"] == "Juan Pérez"
        assert data["estado"] == "pendiente"
        assert data["id"] is not None

    def test_campos_obligatorios_faltantes_devuelve_422(self, client):
        resp = client.post("/api/bookings/", json={"nombre_cliente": "Juan"})
        assert resp.status_code == 422

    def test_conflicto_mismo_slot_devuelve_409(self, client):
        payload = _booking_payload()
        client.post("/api/bookings/", json=payload)
        resp = client.post("/api/bookings/", json=payload)
        assert resp.status_code == 409

    def test_dos_slots_distintos_ok(self, client):
        r1 = client.post("/api/bookings/", json=_booking_payload(fecha_hora=_future_datetime(days=7, hour=10)))
        r2 = client.post("/api/bookings/", json=_booking_payload(fecha_hora=_future_datetime(days=7, hour=11)))
        assert r1.status_code == 201
        assert r2.status_code == 201

    def test_slot_ocupado_aparece_en_disponibilidad(self, client):
        dt = _future_datetime(days=8, hour=10)
        client.post("/api/bookings/", json=_booking_payload(fecha_hora=dt))
        fecha = dt[:10]
        resp = client.get("/api/bookings/disponibilidad", params={"fecha": fecha})
        slots = resp.json()["slots_ocupados"]
        assert len(slots) == 1


# ── GET /api/bookings (admin) ─────────────────────────────────────────────────

class TestListarReservasAdmin:
    def test_sin_token_devuelve_401(self, client):
        resp = client.get("/api/bookings/")
        assert resp.status_code == 401

    def test_con_token_devuelve_lista_paginada(self, client, admin_token):
        client.post("/api/bookings/", json=_booking_payload())
        resp = client.get(
            "/api/bookings/",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_paginacion_size(self, client, admin_token):
        for i in range(3):
            client.post("/api/bookings/", json=_booking_payload(
                fecha_hora=_future_datetime(days=10 + i, hour=10)
            ))
        resp = client.get(
            "/api/bookings/?page=1&size=2",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["items"]) <= 2
        assert data["size"] == 2


# ── GET /api/bookings/{id} (admin) ────────────────────────────────────────────

class TestObtenerReservaAdmin:
    def test_obtiene_reserva_por_id(self, client, admin_token):
        r = client.post("/api/bookings/", json=_booking_payload())
        booking_id = r.json()["id"]
        resp = client.get(
            f"/api/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == booking_id

    def test_id_inexistente_devuelve_404(self, client, admin_token):
        resp = client.get(
            "/api/bookings/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_sin_token_devuelve_401(self, client):
        resp = client.get("/api/bookings/1")
        assert resp.status_code == 401


# ── PATCH /api/bookings/{id} (admin) ─────────────────────────────────────────

class TestActualizarReserva:
    def test_actualiza_estado(self, client, admin_token):
        r = client.post("/api/bookings/", json=_booking_payload())
        booking_id = r.json()["id"]
        resp = client.patch(
            f"/api/bookings/{booking_id}",
            json={"estado": "confirmada"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["estado"] == "confirmada"

    def test_id_inexistente_devuelve_404(self, client, admin_token):
        resp = client.patch(
            "/api/bookings/9999",
            json={"estado": "confirmada"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_sin_token_devuelve_401(self, client):
        resp = client.patch("/api/bookings/1", json={"estado": "confirmada"})
        assert resp.status_code == 401


# ── DELETE /api/bookings/{id} (admin) ────────────────────────────────────────

class TestCancelarReserva:
    def test_cancela_reserva(self, client, admin_token):
        r = client.post("/api/bookings/", json=_booking_payload())
        booking_id = r.json()["id"]
        resp = client.delete(
            f"/api/bookings/{booking_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 204

    def test_id_inexistente_devuelve_404(self, client, admin_token):
        resp = client.delete(
            "/api/bookings/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    def test_sin_token_devuelve_401(self, client):
        resp = client.delete("/api/bookings/1")
        assert resp.status_code == 401
