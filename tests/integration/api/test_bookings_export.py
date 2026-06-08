"""Tests de integración del endpoint GET /api/bookings/export (CSV)."""

import csv
import io

import pytest

from tests.helpers import booking_payload

pytestmark = pytest.mark.usefixtures("seed_booking_service")

# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _sin_smtp(mocker):
    """Inhabilita el notifier SMTP para todos los tests de este módulo."""
    mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_booking(client, fecha_hora: str, nombre: str = "Test Cliente", **kwargs) -> dict:
    payload = booking_payload(nombre_cliente=nombre, fecha_hora=fecha_hora, **kwargs)
    resp = client.post("/api/bookings/", json=payload)
    assert resp.status_code == 201, f"No se pudo crear reserva de test: {resp.text}"
    return resp.json()


def _export(client, auth_headers, desde: str, hasta: str):
    return client.get(
        "/api/bookings/export",
        params={"desde": desde, "hasta": hasta},
        headers=auth_headers,
    )


def _parse_csv(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


# ── Autenticación ──────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_export_sin_token_401(client):
    resp = client.get("/api/bookings/export", params={"desde": "2027-01-01", "hasta": "2027-12-31"})
    assert resp.status_code == 401


# ── Validación de parámetros ───────────────────────────────────────────────────

@pytest.mark.integration
def test_export_sin_params_422(client, auth_headers):
    resp = client.get("/api/bookings/export", headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.integration
def test_export_solo_desde_422(client, auth_headers):
    resp = client.get("/api/bookings/export", params={"desde": "2027-01-01"}, headers=auth_headers)
    assert resp.status_code == 422


@pytest.mark.integration
def test_export_fecha_invalida_422(client, auth_headers):
    resp = client.get(
        "/api/bookings/export",
        params={"desde": "no-es-fecha", "hasta": "2027-12-31"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_export_hasta_menor_que_desde_400(client, auth_headers):
    resp = _export(client, auth_headers, "2027-06-01", "2027-05-01")
    assert resp.status_code == 400


# ── CSV sin datos ─────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_export_rango_vacio_solo_cabecera(client, auth_headers):
    resp = _export(client, auth_headers, "2020-01-01", "2020-01-31")
    assert resp.status_code == 200
    assert len(resp.text.strip().splitlines()) == 1


@pytest.mark.integration
def test_export_cabecera_columnas_correctas(client, auth_headers):
    resp = _export(client, auth_headers, "2020-01-01", "2020-01-31")
    assert resp.status_code == 200
    assert resp.text.strip().splitlines()[0] == "id,nombre_cliente,telefono,servicio,fecha_hora,estado,creada_en"


# ── CSV con datos ─────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_export_incluye_reservas_en_rango(client, auth_headers):
    _make_booking(client, "2027-03-15T10:00:00", nombre="Ana López")
    _make_booking(client, "2027-03-20T11:00:00", nombre="Luis García")
    resp = _export(client, auth_headers, "2027-03-01", "2027-03-31")
    rows = _parse_csv(resp.text)
    assert len(rows) == 2
    nombres = {r["nombre_cliente"] for r in rows}
    assert "Ana López" in nombres
    assert "Luis García" in nombres


@pytest.mark.integration
def test_export_excluye_reservas_fuera_de_rango(client, auth_headers):
    _make_booking(client, "2027-03-15T10:00:00", nombre="Dentro del rango")
    _make_booking(client, "2027-05-01T10:00:00", nombre="Fuera del rango")
    resp = _export(client, auth_headers, "2027-03-01", "2027-03-31")
    rows = _parse_csv(resp.text)
    assert len(rows) == 1
    assert rows[0]["nombre_cliente"] == "Dentro del rango"


@pytest.mark.integration
def test_export_reservas_ordenadas_por_fecha_ascendente(client, auth_headers):
    _make_booking(client, "2027-04-20T15:00:00", nombre="Tercera")
    _make_booking(client, "2027-04-10T09:00:00", nombre="Primera")
    _make_booking(client, "2027-04-15T12:00:00", nombre="Segunda")
    resp = _export(client, auth_headers, "2027-04-01", "2027-04-30")
    rows = _parse_csv(resp.text)
    assert rows[0]["nombre_cliente"] == "Primera"
    assert rows[1]["nombre_cliente"] == "Segunda"
    assert rows[2]["nombre_cliente"] == "Tercera"


@pytest.mark.integration
def test_export_columnas_tienen_datos_correctos(client, auth_headers):
    _make_booking(client, "2027-06-10T14:00:00", nombre="María Ruiz",
                  telefono="611222333")
    resp = _export(client, auth_headers, "2027-06-01", "2027-06-30")
    rows = _parse_csv(resp.text)
    row = rows[0]
    assert row["nombre_cliente"] == "María Ruiz"
    assert row["telefono"] == "611222333"
    assert row["servicio"] == "Corte Clásico"
    assert row["estado"] == "pendiente"
    assert "2027-06-10" in row["fecha_hora"]
    assert row["id"].isdigit()


@pytest.mark.integration
def test_export_mismo_dia_inicio_y_fin(client, auth_headers):
    _make_booking(client, "2027-07-15T09:00:00")
    _make_booking(client, "2027-07-15T17:00:00")
    resp = _export(client, auth_headers, "2027-07-15", "2027-07-15")
    assert len(_parse_csv(resp.text)) == 2


# ── Headers HTTP ──────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_export_content_type_csv(client, auth_headers):
    resp = _export(client, auth_headers, "2027-01-01", "2027-01-31")
    assert "text/csv" in resp.headers.get("content-type", "")


@pytest.mark.integration
def test_export_content_disposition_nombre_correcto(client, auth_headers):
    resp = _export(client, auth_headers, "2027-03-01", "2027-03-31")
    cd = resp.headers.get("content-disposition", "")
    assert "attachment" in cd
    assert "reservas_2027-03-01_2027-03-31.csv" in cd
