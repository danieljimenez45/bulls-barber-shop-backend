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
