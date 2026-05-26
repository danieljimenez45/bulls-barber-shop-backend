"""Tests de integración del endpoint de galería."""

import io

import pytest
from PIL import Image


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_png_bytes(width: int = 10, height: int = 10) -> bytes:
    """Genera un PNG mínimo válido en memoria usando Pillow."""
    buf = io.BytesIO()
    Image.new("RGB", (width, height), color=(200, 0, 0)).save(buf, format="PNG")
    return buf.getvalue()


def _upload(client, auth_headers, file_data: bytes, filename: str, mocker):
    """Envía una petición multipart de upload mockeando el almacenamiento."""
    mock_storage = mocker.Mock()
    mock_storage.save.return_value = "https://example.com/test.png"
    mocker.patch("app.api.routers.gallery.get_file_storage", return_value=mock_storage)

    return client.post(
        "/api/gallery/upload",
        headers=auth_headers,
        files={"file": (filename, file_data, "image/png")},
        data={"categoria": "corte"},
    )


# ── Tests: rechazo por tamaño ─────────────────────────────────────────────────

@pytest.mark.integration
def test_upload_rechaza_archivo_mayor_5mb(client, auth_headers, mocker):
    """Archivos mayores a 5 MB deben ser rechazados con 400."""
    big_data = b"x" * (5 * 1024 * 1024 + 1)
    response = _upload(client, auth_headers, big_data, "foto.png", mocker)
    assert response.status_code == 400
    assert "5 MB" in response.json()["detail"]


# ── Tests: rechazo por extensión ──────────────────────────────────────────────

@pytest.mark.integration
def test_upload_rechaza_extension_no_permitida(client, auth_headers, mocker):
    """Extensiones fuera de la lista blanca (.txt) deben ser rechazadas con 400."""
    response = _upload(client, auth_headers, b"contenido", "documento.txt", mocker)
    assert response.status_code == 400
    assert "Extensión no permitida" in response.json()["detail"]


@pytest.mark.integration
def test_upload_rechaza_doble_extension(client, auth_headers, mocker):
    """Nombres con doble extensión (foto.png.exe) deben ser rechazados con 400."""
    response = _upload(client, auth_headers, _make_png_bytes(), "foto.png.exe", mocker)
    assert response.status_code == 400
    assert "doble extensión" in response.json()["detail"]


# ── Tests: rechazo por contenido ──────────────────────────────────────────────

@pytest.mark.integration
def test_upload_rechaza_contenido_no_imagen(client, auth_headers, mocker):
    """Bytes que no son imagen real (aunque tengan extensión .png) deben rechazarse con 400."""
    fake_data = b"esto no es una imagen"
    response = _upload(client, auth_headers, fake_data, "trampa.png", mocker)
    assert response.status_code == 400
    assert "imagen válida" in response.json()["detail"]


# ── Tests: upload válido ───────────────────────────────────────────────────────

@pytest.mark.integration
def test_upload_png_valido_201(client, auth_headers, mocker):
    """Una imagen PNG real con extensión permitida debe subirse correctamente."""
    response = _upload(client, auth_headers, _make_png_bytes(), "corte.png", mocker)
    assert response.status_code == 201
    data = response.json()
    assert "imagen_url" in data
    assert data["categoria"] == "corte"


@pytest.mark.integration
def test_upload_sin_token_401(client, mocker):
    """El endpoint de upload requiere autenticación de administrador."""
    mock_storage = mocker.Mock()
    mocker.patch("app.api.routers.gallery.get_file_storage", return_value=mock_storage)
    response = client.post(
        "/api/gallery/upload",
        files={"file": ("foto.png", _make_png_bytes(), "image/png")},
        data={"categoria": "corte"},
    )
    assert response.status_code == 401


# ── Listado y filtros ─────────────────────────────────────────────────────────

@pytest.mark.integration
def test_lista_vacia_inicialmente(client):
    """Con la BD vacía el listado de galería devuelve total=0."""
    resp = client.get("/api/gallery/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.integration
def test_paginacion_devuelve_valores_por_defecto(client):
    """Sin parámetros de paginación deben devolverse page=1 y size=20."""
    resp = client.get("/api/gallery/")
    data = resp.json()
    assert data["page"] == 1
    assert data["size"] == 20


@pytest.mark.integration
def test_paginacion_personalizada(client, db_session):
    """Con 3 imágenes y size=2 se devuelven 2 items y pages=2."""
    from app.infrastructure.persistence.orm.gallery import GalleryORM

    for i in range(3):
        db_session.add(GalleryORM(
            imagen_url=f"/uploads/img{i}.jpg",
            titulo=f"Imagen {i}",
            categoria="corte",
            visible=True,
        ))
    db_session.commit()

    resp = client.get("/api/gallery/?page=1&size=2")
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2


@pytest.mark.integration
def test_filtra_por_categoria(client, db_session):
    """El parámetro ?categoria= debe filtrar las imágenes por categoría."""
    from app.infrastructure.persistence.orm.gallery import GalleryORM

    db_session.add(GalleryORM(imagen_url="/uploads/corte.jpg", categoria="corte", visible=True))
    db_session.add(GalleryORM(imagen_url="/uploads/barba.jpg", categoria="barba", visible=True))
    db_session.commit()

    resp = client.get("/api/gallery/?categoria=barba")
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["categoria"] == "barba"


@pytest.mark.integration
def test_imagenes_no_visibles_no_aparecen(client, db_session):
    """Las imágenes con visible=False no deben aparecer en el listado público."""
    from app.infrastructure.persistence.orm.gallery import GalleryORM

    db_session.add(GalleryORM(imagen_url="/uploads/visible.jpg", categoria="corte", visible=True))
    db_session.add(GalleryORM(imagen_url="/uploads/oculta.jpg", categoria="corte", visible=False))
    db_session.commit()

    resp = client.get("/api/gallery/")
    assert resp.json()["total"] == 1


# ── Eliminar: not found ────────────────────────────────────────────────────────

@pytest.mark.integration
def test_eliminar_imagen_id_inexistente_404(client, auth_headers, mocker):
    """DELETE con un ID inexistente debe devolver 404."""
    mock_storage = mocker.Mock()
    mocker.patch("app.api.routers.gallery.get_file_storage", return_value=mock_storage)
    resp = client.delete("/api/gallery/9999", headers=auth_headers)
    assert resp.status_code == 404
