"""Tests de integración de la API de servicios."""

import pytest

from tests.helpers import service_payload


@pytest.mark.integration
def test_listar_servicios_publico_200(client):
    response = client.get("/api/services/")
    assert response.status_code == 200


@pytest.mark.integration
def test_listar_servicios_solo_activos_por_defecto(client, auth_headers):
    # Crear un servicio activo y uno inactivo
    client.post("/api/services/", headers=auth_headers, json=service_payload(nombre="Activo", activo=True))
    client.post("/api/services/", headers=auth_headers, json=service_payload(nombre="Inactivo", activo=False))
    response = client.get("/api/services/")
    data = response.json()
    nombres = [s["nombre"] for s in data]
    assert "Inactivo" not in nombres


@pytest.mark.integration
def test_crear_servicio_sin_token_401(client):
    response = client.post("/api/services/", json=service_payload())
    assert response.status_code == 401


@pytest.mark.integration
def test_crear_servicio_con_token_201(client, auth_headers):
    response = client.post("/api/services/", headers=auth_headers, json=service_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Corte Clásico"
    assert data["precio"] == 15.0


@pytest.mark.integration
def test_actualizar_servicio(client, auth_headers):
    created = client.post("/api/services/", headers=auth_headers, json=service_payload()).json()
    svc_id = created["id"]
    response = client.put(
        f"/api/services/{svc_id}",
        headers=auth_headers,
        json={**service_payload(), "nombre": "Corte Moderno", "precio": 20.0},
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == "Corte Moderno"


@pytest.mark.integration
def test_eliminar_servicio(client, auth_headers):
    created = client.post("/api/services/", headers=auth_headers, json=service_payload()).json()
    svc_id = created["id"]
    response = client.delete(f"/api/services/{svc_id}", headers=auth_headers)
    assert response.status_code in (200, 204)


@pytest.mark.integration
def test_listar_servicios_solo_activos_false_sin_token_401(client):
    """Listar servicios inactivos sin JWT debe devolver 401."""
    response = client.get("/api/services/", params={"solo_activos": False})
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_servicios_solo_activos_false_token_invalido_401(client):
    """Token inválido con solo_activos=false debe devolver 401 (no tratar como anónimo)."""
    response = client.get(
        "/api/services/",
        params={"solo_activos": False},
        headers={"Authorization": "Bearer token_falso"},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_servicios_solo_activos_false_con_token_200(client, auth_headers):
    """Con JWT válido el admin puede ver todos los servicios, incluyendo los inactivos."""
    client.post(
        "/api/services/",
        headers=auth_headers,
        json=service_payload(nombre="Servicio Inactivo", activo=False),
    )
    response = client.get(
        "/api/services/",
        headers=auth_headers,
        params={"solo_activos": False},
    )
    assert response.status_code == 200
    nombres = [s["nombre"] for s in response.json()]
    assert "Servicio Inactivo" in nombres


# ── Listado y filtros adicionales ─────────────────────────────────────────────

@pytest.mark.integration
def test_lista_vacia_inicialmente(client):
    """Con la BD vacía el listado de servicios debe estar vacío."""
    resp = client.get("/api/services/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.integration
def test_filtra_por_categoria(client, auth_headers):
    """El parámetro ?categoria= debe filtrar los servicios por su categoría."""
    client.post("/api/services/", headers=auth_headers, json=service_payload(categoria="corte"))
    client.post(
        "/api/services/",
        headers=auth_headers,
        json=service_payload(nombre="Barba", categoria="barba"),
    )
    resp = client.get("/api/services/?categoria=barba")
    data = resp.json()
    assert len(data) == 1
    assert data[0]["categoria"] == "barba"


# ── Obtener por ID ─────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_get_servicio_por_id_200(client, auth_headers):
    """GET /api/services/{id} debe devolver el servicio correcto."""
    created = client.post("/api/services/", headers=auth_headers, json=service_payload()).json()
    resp = client.get(f"/api/services/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Corte Clásico"


@pytest.mark.integration
def test_get_servicio_id_inexistente_404(client):
    """GET con un ID inexistente debe devolver 404."""
    resp = client.get("/api/services/9999")
    assert resp.status_code == 404


# ── Validaciones de schema adicionales ────────────────────────────────────────

@pytest.mark.integration
def test_crear_servicio_precio_y_nombre_obligatorios_422(client, auth_headers):
    """Crear servicio sin nombre ni precio debe devolver 422."""
    resp = client.post(
        "/api/services/",
        headers=auth_headers,
        json={"descripcion": "sin nombre ni precio"},
    )
    assert resp.status_code == 422


# ── Actualizar: not found ──────────────────────────────────────────────────────

@pytest.mark.integration
def test_actualizar_servicio_id_inexistente_404(client, auth_headers):
    """PUT con un ID inexistente debe devolver 404."""
    resp = client.put(
        "/api/services/9999",
        headers=auth_headers,
        json={**service_payload(), "nombre": "No existe"},
    )
    assert resp.status_code == 404


# ── Eliminar: not found + verificación ────────────────────────────────────────

@pytest.mark.integration
def test_eliminar_servicio_verifica_con_get(client, auth_headers):
    """Tras eliminar un servicio, el GET por ID debe devolver 404."""
    created = client.post("/api/services/", headers=auth_headers, json=service_payload()).json()
    client.delete(f"/api/services/{created['id']}", headers=auth_headers)
    resp = client.get(f"/api/services/{created['id']}")
    assert resp.status_code == 404


@pytest.mark.integration
def test_eliminar_servicio_id_inexistente_404(client, auth_headers):
    """DELETE con un ID inexistente debe devolver 404."""
    resp = client.delete("/api/services/9999", headers=auth_headers)
    assert resp.status_code == 404
