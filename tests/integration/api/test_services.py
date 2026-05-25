"""Tests de integración de la API de servicios."""

import pytest


def _payload(**kwargs):
    defaults = {
        "nombre": "Corte Clásico",
        "precio": 15.0,
        "descripcion": "Corte de pelo clásico",
        "duracion_minutos": 30,
        "categoria": "corte",
        "activo": True,
        "orden": 0,
    }
    defaults.update(kwargs)
    return defaults


@pytest.mark.integration
def test_listar_servicios_publico_200(client):
    response = client.get("/api/services/")
    assert response.status_code == 200


@pytest.mark.integration
def test_listar_servicios_solo_activos_por_defecto(client, auth_headers):
    # Crear un servicio activo y uno inactivo
    client.post("/api/services/", headers=auth_headers, json=_payload(nombre="Activo", activo=True))
    client.post("/api/services/", headers=auth_headers, json=_payload(nombre="Inactivo", activo=False))
    response = client.get("/api/services/")
    data = response.json()
    nombres = [s["nombre"] for s in data]
    assert "Inactivo" not in nombres


@pytest.mark.integration
def test_crear_servicio_sin_token_401(client):
    response = client.post("/api/services/", json=_payload())
    assert response.status_code == 401


@pytest.mark.integration
def test_crear_servicio_con_token_201(client, auth_headers):
    response = client.post("/api/services/", headers=auth_headers, json=_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Corte Clásico"
    assert data["precio"] == 15.0


@pytest.mark.integration
def test_actualizar_servicio(client, auth_headers):
    created = client.post("/api/services/", headers=auth_headers, json=_payload()).json()
    svc_id = created["id"]
    response = client.put(
        f"/api/services/{svc_id}",
        headers=auth_headers,
        json={**_payload(), "nombre": "Corte Moderno", "precio": 20.0},
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == "Corte Moderno"


@pytest.mark.integration
def test_eliminar_servicio(client, auth_headers):
    created = client.post("/api/services/", headers=auth_headers, json=_payload()).json()
    svc_id = created["id"]
    response = client.delete(f"/api/services/{svc_id}", headers=auth_headers)
    assert response.status_code in (200, 204)


@pytest.mark.integration
def test_listar_servicios_solo_activos_false_sin_token_401(client):
    """Listar servicios inactivos sin JWT debe devolver 401."""
    response = client.get("/api/services/", params={"solo_activos": False})
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_servicios_solo_activos_false_con_token_200(client, auth_headers):
    """Con JWT válido el admin puede ver todos los servicios, incluyendo los inactivos."""
    client.post(
        "/api/services/",
        headers=auth_headers,
        json=_payload(nombre="Servicio Inactivo", activo=False),
    )
    response = client.get(
        "/api/services/",
        headers=auth_headers,
        params={"solo_activos": False},
    )
    assert response.status_code == 200
    nombres = [s["nombre"] for s in response.json()]
    assert "Servicio Inactivo" in nombres
