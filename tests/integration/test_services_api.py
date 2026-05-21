"""Tests de integración para el endpoint /api/services."""


def _service_payload(**kwargs) -> dict:
    base = {
        "nombre": "Corte clásico",
        "precio": 15.0,
        "duracion_minutos": 30,
        "categoria": "corte",
        "activo": True,
        "orden": 0,
    }
    base.update(kwargs)
    return base


class TestListarServicios:
    def test_lista_vacia_inicialmente(self, client):
        resp = client.get("/api/services/")
        assert resp.status_code == 200
        data = resp.json()
        assert data == []

    def test_devuelve_servicios_creados(self, client, admin_token):
        client.post(
            "/api/services/",
            json=_service_payload(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get("/api/services/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_filtra_por_categoria(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post("/api/services/", json=_service_payload(categoria="corte"), headers=headers)
        client.post("/api/services/", json=_service_payload(nombre="Barba", categoria="barba"), headers=headers)

        resp = client.get("/api/services/?categoria=barba")
        data = resp.json()
        assert len(data) == 1
        assert data[0]["categoria"] == "barba"

    def test_solo_activos_por_defecto(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post("/api/services/", json=_service_payload(activo=True), headers=headers)
        client.post("/api/services/", json=_service_payload(nombre="Inactivo", activo=False), headers=headers)

        resp = client.get("/api/services/")
        data = resp.json()
        assert all(s["activo"] for s in data)

    def test_incluye_inactivos_con_flag(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post("/api/services/", json=_service_payload(activo=True), headers=headers)
        client.post("/api/services/", json=_service_payload(nombre="Inactivo", activo=False), headers=headers)

        resp = client.get("/api/services/?solo_activos=false")
        assert len(resp.json()) == 2


class TestObtenerServicio:
    def test_devuelve_servicio_por_id(self, client, admin_token):
        r = client.post(
            "/api/services/",
            json=_service_payload(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        service_id = r.json()["id"]
        resp = client.get(f"/api/services/{service_id}")
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Corte clásico"

    def test_id_inexistente_devuelve_404(self, client):
        resp = client.get("/api/services/9999")
        assert resp.status_code == 404


class TestCrearServicio:
    def test_sin_token_devuelve_401(self, client):
        resp = client.post("/api/services/", json=_service_payload())
        assert resp.status_code == 401

    def test_crea_correctamente(self, client, admin_token):
        resp = client.post(
            "/api/services/",
            json=_service_payload(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Corte clásico"
        assert data["precio"] == 15.0
        assert data["activo"] is True
        assert "id" in data

    def test_precio_y_nombre_obligatorios(self, client, admin_token):
        resp = client.post(
            "/api/services/",
            json={"descripcion": "sin nombre ni precio"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422


class TestActualizarServicio:
    def test_sin_token_devuelve_401(self, client, admin_token):
        r = client.post(
            "/api/services/",
            json=_service_payload(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        service_id = r.json()["id"]
        resp = client.put(f"/api/services/{service_id}", json={"nombre": "Nuevo nombre"})
        assert resp.status_code == 401

    def test_actualiza_correctamente(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = client.post("/api/services/", json=_service_payload(), headers=headers)
        service_id = r.json()["id"]

        resp = client.put(
            f"/api/services/{service_id}",
            json={"nombre": "Corte premium", "precio": 20.0},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["nombre"] == "Corte premium"
        assert data["precio"] == 20.0

    def test_id_inexistente_devuelve_404(self, client, admin_token):
        resp = client.put(
            "/api/services/9999",
            json={"nombre": "No existe"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestEliminarServicio:
    def test_sin_token_devuelve_401(self, client, admin_token):
        r = client.post(
            "/api/services/",
            json=_service_payload(),
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        service_id = r.json()["id"]
        resp = client.delete(f"/api/services/{service_id}")
        assert resp.status_code == 401

    def test_elimina_correctamente(self, client, admin_token):
        headers = {"Authorization": f"Bearer {admin_token}"}
        r = client.post("/api/services/", json=_service_payload(), headers=headers)
        service_id = r.json()["id"]

        resp = client.delete(f"/api/services/{service_id}", headers=headers)
        assert resp.status_code == 204

        resp_get = client.get(f"/api/services/{service_id}")
        assert resp_get.status_code == 404

    def test_id_inexistente_devuelve_404(self, client, admin_token):
        resp = client.delete(
            "/api/services/9999",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404
