"""Tests de integración de la API de reseñas."""

import pytest

from tests.helpers import review_payload


@pytest.mark.integration
def test_listar_reviews_publico_solo_visibles(client, auth_headers):
    # Crear dos reseñas (visible=True por defecto)
    r1 = client.post("/api/reviews/", json=review_payload(nombre="Ana")).json()
    r2 = client.post("/api/reviews/", json=review_payload(nombre="Bob")).json()
    # Ocultar r2: el endpoint requiere ?visible=false
    client.patch(
        f"/api/reviews/{r2['id']}/visibilidad",
        headers=auth_headers,
        params={"visible": False},
    )
    # La lista pública solo debe mostrar las visibles
    response = client.get("/api/reviews/")
    assert response.status_code == 200
    nombres = [r["nombre"] for r in response.json()["items"]]
    assert "Ana" in nombres
    assert "Bob" not in nombres


@pytest.mark.integration
def test_crear_review_publico_201(client):
    response = client.post("/api/reviews/", json=review_payload())
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Cliente Satisfecho"
    assert data["valoracion"] == 5


@pytest.mark.integration
def test_toggle_visibilidad_sin_token_401(client):
    created = client.post("/api/reviews/", json=review_payload()).json()
    # Sin token → 401
    response = client.patch(
        f"/api/reviews/{created['id']}/visibilidad",
        params={"visible": False},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_toggle_visibilidad_con_token(client, auth_headers):
    created = client.post("/api/reviews/", json=review_payload()).json()
    visible_inicial = created["visible"]
    # Invertir visibilidad
    nueva_visibilidad = not visible_inicial
    response = client.patch(
        f"/api/reviews/{created['id']}/visibilidad",
        headers=auth_headers,
        params={"visible": nueva_visibilidad},
    )
    assert response.status_code == 200
    assert response.json()["visible"] == nueva_visibilidad


@pytest.mark.integration
def test_eliminar_review(client, auth_headers):
    created = client.post("/api/reviews/", json=review_payload()).json()
    response = client.delete(f"/api/reviews/{created['id']}", headers=auth_headers)
    assert response.status_code in (200, 204)


@pytest.mark.integration
def test_listar_reviews_solo_visibles_false_token_invalido_401(client):
    response = client.get(
        "/api/reviews/",
        params={"solo_visibles": False},
        headers={"Authorization": "Bearer token_falso"},
    )
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_reviews_solo_visibles_false_sin_token_401(client):
    """Listar reseñas ocultas sin JWT debe devolver 401."""
    response = client.get("/api/reviews/", params={"solo_visibles": False})
    assert response.status_code == 401


@pytest.mark.integration
def test_listar_reviews_solo_visibles_false_con_token_200(client, auth_headers):
    """Con JWT válido el admin puede ver todas las reseñas, incluyendo las ocultas."""
    client.post("/api/reviews/", json=review_payload(nombre="Visible"))
    response = client.get(
        "/api/reviews/",
        headers=auth_headers,
        params={"solo_visibles": False},
    )
    assert response.status_code == 200


# ── Validaciones de schema ─────────────────────────────────────────────────────

@pytest.mark.integration
def test_crear_review_nombre_demasiado_corto_422(client):
    """Nombre con menos de 2 caracteres debe devolver 422."""
    response = client.post("/api/reviews/", json=review_payload(nombre="X"))
    assert response.status_code == 422


@pytest.mark.integration
def test_crear_review_nombre_demasiado_largo_422(client):
    """Nombre con más de 100 caracteres debe devolver 422."""
    response = client.post("/api/reviews/", json=review_payload(nombre="A" * 101))
    assert response.status_code == 422


@pytest.mark.integration
def test_crear_review_valoracion_fuera_de_rango_422(client):
    """Valoración fuera del rango [1, 5] debe devolver 422."""
    response_alta = client.post("/api/reviews/", json=review_payload(valoracion=6))
    assert response_alta.status_code == 422
    response_baja = client.post("/api/reviews/", json=review_payload(valoracion=0))
    assert response_baja.status_code == 422


@pytest.mark.integration
def test_crear_review_comentario_demasiado_largo_422(client):
    """Comentario con más de 1000 caracteres debe devolver 422."""
    response = client.post("/api/reviews/", json=review_payload(comentario="C" * 1001))
    assert response.status_code == 422


# ── Paginación ─────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_lista_vacia_devuelve_total_cero(client):
    """Con la BD vacía el listado público devuelve total=0."""
    resp = client.get("/api/reviews/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.integration
def test_paginacion_devuelve_valores_por_defecto(client):
    """Sin parámetros de paginación deben devolverse page=1 y size=20."""
    resp = client.get("/api/reviews/")
    data = resp.json()
    assert data["page"] == 1
    assert data["size"] == 20


@pytest.mark.integration
def test_paginacion_personalizada(client):
    """Con 3 reseñas y size=2 se devuelven 2 items y pages=2."""
    for i in range(3):
        client.post("/api/reviews/", json=review_payload(nombre=f"Cliente {i}"))
    resp = client.get("/api/reviews/?page=1&size=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2


# ── Not found ──────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_toggle_visibilidad_id_inexistente_404(client, auth_headers):
    """Cambiar visibilidad de una reseña inexistente debe devolver 404."""
    resp = client.patch(
        "/api/reviews/9999/visibilidad",
        params={"visible": False},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.integration
def test_eliminar_id_inexistente_404(client, auth_headers):
    """Eliminar una reseña inexistente debe devolver 404."""
    resp = client.delete("/api/reviews/9999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.integration
def test_resena_eliminada_no_aparece_en_listado(client, auth_headers):
    """Tras eliminar una reseña no debe aparecer en el listado público."""
    created = client.post("/api/reviews/", json=review_payload()).json()
    client.delete(f"/api/reviews/{created['id']}", headers=auth_headers)
    resp = client.get("/api/reviews/")
    assert resp.json()["total"] == 0
