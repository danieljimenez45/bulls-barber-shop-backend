"""Tests de integración para el endpoint /api/reviews."""


def _review_payload(**kwargs) -> dict:
    base = {"nombre": "Ana García", "valoracion": 5, "comentario": "Excelente servicio"}
    base.update(kwargs)
    return base


class TestListarResenas:
    def test_lista_vacia_inicialmente(self, client):
        resp = client.get("/api/reviews/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_paginacion_por_defecto(self, client):
        resp = client.get("/api/reviews/")
        data = resp.json()
        assert data["page"] == 1
        assert data["size"] == 20

    def test_paginacion_personalizada(self, client):
        for i in range(3):
            client.post("/api/reviews/", json=_review_payload(nombre=f"Cliente {i}"))
        resp = client.get("/api/reviews/?page=1&size=2")
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2


class TestCrearResena:
    def test_crea_correctamente(self, client):
        resp = client.post("/api/reviews/", json=_review_payload())
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Ana García"
        assert data["valoracion"] == 5
        assert data["visible"] is True

    def test_valoracion_fuera_de_rango_devuelve_error(self, client):
        resp = client.post("/api/reviews/", json=_review_payload(valoracion=6))
        assert resp.status_code in (400, 422)

    def test_valoracion_cero_devuelve_error(self, client):
        resp = client.post("/api/reviews/", json=_review_payload(valoracion=0))
        assert resp.status_code in (400, 422)

    def test_nombre_obligatorio(self, client):
        resp = client.post("/api/reviews/", json={"valoracion": 5})
        assert resp.status_code == 422


class TestVisibilidadResena:
    def test_ocultar_resena_requiere_admin(self, client):
        r = client.post("/api/reviews/", json=_review_payload())
        review_id = r.json()["id"]
        resp = client.patch(f"/api/reviews/{review_id}/visibilidad", params={"visible": False})
        assert resp.status_code == 401

    def test_ocultar_con_token(self, client, admin_token):
        r = client.post("/api/reviews/", json=_review_payload())
        review_id = r.json()["id"]
        resp = client.patch(
            f"/api/reviews/{review_id}/visibilidad",
            params={"visible": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["visible"] is False

    def test_resena_oculta_no_aparece_en_listado_publico(self, client, admin_token):
        r = client.post("/api/reviews/", json=_review_payload())
        review_id = r.json()["id"]
        client.patch(
            f"/api/reviews/{review_id}/visibilidad",
            params={"visible": False},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        resp = client.get("/api/reviews/")
        assert resp.json()["total"] == 0
