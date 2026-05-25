"""Tests de integración para el endpoint /api/contact."""


def _contact_payload(**kwargs) -> dict:
    base = {
        "nombre": "Pedro",
        "email": "pedro@example.com",
        "telefono": "600000002",
        "asunto": "Consulta",
        "mensaje": "¿Abrís los domingos?",
    }
    base.update(kwargs)
    return base


class TestContacto:
    def test_envia_mensaje_correctamente(self, client, mocker):
        mocker.patch(
            "app.api.routers.contact.SMTPContactNotifier",
            return_value=mocker.Mock(),
        )
        resp = client.post("/api/contact/", json=_contact_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["ok"] is True
        assert data["id"] is not None

    def test_nombre_obligatorio(self, client):
        payload = _contact_payload()
        del payload["nombre"]
        resp = client.post("/api/contact/", json=payload)
        assert resp.status_code == 422

    def test_email_obligatorio(self, client):
        payload = _contact_payload()
        del payload["email"]
        resp = client.post("/api/contact/", json=payload)
        assert resp.status_code == 422

    def test_mensaje_obligatorio(self, client):
        payload = _contact_payload()
        del payload["mensaje"]
        resp = client.post("/api/contact/", json=payload)
        assert resp.status_code == 422

    def test_email_invalido_devuelve_422(self, client):
        resp = client.post("/api/contact/", json=_contact_payload(email="no-es-email"))
        assert resp.status_code == 422
