"""Tests de integración de la API de contacto."""

import pytest


def _payload(**kwargs):
    defaults = {
        "nombre": "Carlos Ruiz",
        "email": "carlos@example.com",
        "mensaje": "Quiero información sobre precios.",
    }
    defaults.update(kwargs)
    return defaults


@pytest.mark.integration
def test_enviar_mensaje_publico_201(client, mocker):
    mocker.patch(
        "app.api.routers.contact.SMTPContactNotifier",
        return_value=mocker.Mock(),
    )
    response = client.post("/api/contact/", json=_payload())
    assert response.status_code == 201
    data = response.json()
    # El endpoint devuelve {"ok": True, "id": ..., "mensaje": "..."}
    assert data["ok"] is True
    assert data["id"] is not None


@pytest.mark.integration
def test_enviar_mensaje_campos_invalidos_422(client):
    response = client.post("/api/contact/", json={"nombre": "Solo nombre"})
    assert response.status_code == 422


@pytest.mark.integration
def test_listar_mensajes_sin_token_401(client):
    response = client.get("/api/contact/")
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_mensajes_con_token_200(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.contact.SMTPContactNotifier",
        return_value=mocker.Mock(),
    )
    client.post("/api/contact/", json=_payload())
    response = client.get("/api/contact/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data or isinstance(data, list)


@pytest.mark.integration
def test_marcar_como_leido(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.contact.SMTPContactNotifier",
        return_value=mocker.Mock(),
    )
    created = client.post("/api/contact/", json=_payload()).json()
    msg_id = created["id"]
    response = client.patch(f"/api/contact/{msg_id}/leido", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["leido"] is True


@pytest.mark.integration
def test_filtro_solo_no_leidos(client, auth_headers, mocker):
    mocker.patch(
        "app.api.routers.contact.SMTPContactNotifier",
        return_value=mocker.Mock(),
    )
    client.post("/api/contact/", json=_payload(nombre="A"))
    created_b = client.post("/api/contact/", json=_payload(nombre="B")).json()
    # Marcar B como leído
    client.patch(f"/api/contact/{created_b['id']}/leido", headers=auth_headers)
    response = client.get("/api/contact/", headers=auth_headers, params={"solo_no_leidos": True})
    assert response.status_code == 200
