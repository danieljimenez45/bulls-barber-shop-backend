"""
Tests de integración para GET /api/bookings/export

Cubre:
  - Protección de autenticación (401 sin token)
  - Rango sin reservas → solo cabecera CSV
  - Rango con reservas → filas correctas
  - Reservas fuera del rango no se incluyen
  - Rango inválido (hasta < desde) → 400
  - Sin parámetros → 422
  - Content-Disposition con el nombre de fichero correcto
  - Columnas del CSV en el orden correcto
"""

import csv
import io


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_booking(client, fecha_hora: str, nombre: str = "Test Cliente", **kwargs) -> dict:
    """Crea una reserva y devuelve el JSON de respuesta."""
    payload = {
        "nombre_cliente": nombre,
        "telefono": "600000000",
        "servicio_id": 1,
        "servicio_nombre": "Corte clásico",
        "fecha_hora": fecha_hora,
    }
    payload.update(kwargs)
    resp = client.post("/api/bookings/", json=payload)
    assert resp.status_code == 201, f"No se pudo crear reserva de test: {resp.text}"
    return resp.json()


def _export(client, admin_token: str, desde: str, hasta: str):
    """Llama al endpoint de exportación y devuelve la Response."""
    return client.get(
        "/api/bookings/export",
        params={"desde": desde, "hasta": hasta},
        headers={"Authorization": f"Bearer {admin_token}"},
    )


def _parse_csv(text: str) -> list[dict]:
    """Parsea el CSV de respuesta en una lista de dicts."""
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestExportarReservasCSV:

    # ── Autenticación ─────────────────────────────────────────────────────────

    def test_sin_token_devuelve_401(self, client):
        resp = client.get(
            "/api/bookings/export",
            params={"desde": "2027-01-01", "hasta": "2027-12-31"},
        )
        assert resp.status_code == 401

    # ── Validación de parámetros ──────────────────────────────────────────────

    def test_sin_params_devuelve_422(self, client, admin_token):
        resp = client.get(
            "/api/bookings/export",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_solo_desde_devuelve_422(self, client, admin_token):
        resp = client.get(
            "/api/bookings/export",
            params={"desde": "2027-01-01"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_fecha_invalida_devuelve_422(self, client, admin_token):
        resp = client.get(
            "/api/bookings/export",
            params={"desde": "no-es-fecha", "hasta": "2027-12-31"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    def test_hasta_menor_que_desde_devuelve_400(self, client, admin_token):
        resp = _export(client, admin_token, "2027-06-01", "2027-05-01")
        assert resp.status_code == 400

    # ── CSV con rango vacío ───────────────────────────────────────────────────

    def test_rango_sin_reservas_devuelve_solo_cabecera(self, client, admin_token):
        resp = _export(client, admin_token, "2020-01-01", "2020-01-31")
        assert resp.status_code == 200
        lines = resp.text.strip().splitlines()
        assert len(lines) == 1  # solo la fila de cabecera

    def test_cabecera_tiene_columnas_correctas(self, client, admin_token):
        resp = _export(client, admin_token, "2020-01-01", "2020-01-31")
        assert resp.status_code == 200
        cabecera = resp.text.strip().splitlines()[0]
        assert cabecera == "id,nombre_cliente,telefono,servicio,fecha_hora,estado,creada_en"

    # ── CSV con datos ─────────────────────────────────────────────────────────

    def test_incluye_reservas_en_el_rango(self, client, admin_token):
        _make_booking(client, "2027-03-15T10:00:00", nombre="Ana López")
        _make_booking(client, "2027-03-20T11:00:00", nombre="Luis García")

        resp = _export(client, admin_token, "2027-03-01", "2027-03-31")
        assert resp.status_code == 200
        rows = _parse_csv(resp.text)
        assert len(rows) == 2
        nombres = {r["nombre_cliente"] for r in rows}
        assert "Ana López" in nombres
        assert "Luis García" in nombres

    def test_excluye_reservas_fuera_del_rango(self, client, admin_token):
        _make_booking(client, "2027-03-15T10:00:00", nombre="Dentro del rango")
        _make_booking(client, "2027-05-01T10:00:00", nombre="Fuera del rango")

        resp = _export(client, admin_token, "2027-03-01", "2027-03-31")
        assert resp.status_code == 200
        rows = _parse_csv(resp.text)
        assert len(rows) == 1
        assert rows[0]["nombre_cliente"] == "Dentro del rango"

    def test_reservas_ordenadas_por_fecha_ascendente(self, client, admin_token):
        _make_booking(client, "2027-04-20T15:00:00", nombre="Tercera")
        _make_booking(client, "2027-04-10T09:00:00", nombre="Primera")
        _make_booking(client, "2027-04-15T12:00:00", nombre="Segunda")

        resp = _export(client, admin_token, "2027-04-01", "2027-04-30")
        assert resp.status_code == 200
        rows = _parse_csv(resp.text)
        assert len(rows) == 3
        assert rows[0]["nombre_cliente"] == "Primera"
        assert rows[1]["nombre_cliente"] == "Segunda"
        assert rows[2]["nombre_cliente"] == "Tercera"

    def test_columnas_tienen_datos_correctos(self, client, admin_token):
        _make_booking(
            client,
            "2027-06-10T14:00:00",
            nombre="María Ruiz",
            servicio_nombre="Corte clásico",
            telefono="611222333",
        )
        resp = _export(client, admin_token, "2027-06-01", "2027-06-30")
        assert resp.status_code == 200
        rows = _parse_csv(resp.text)
        assert len(rows) == 1
        row = rows[0]
        assert row["nombre_cliente"] == "María Ruiz"
        assert row["telefono"] == "611222333"
        assert row["servicio"] == "Corte clásico"
        assert row["estado"] == "pendiente"
        assert "2027-06-10" in row["fecha_hora"]
        assert row["id"].isdigit()

    def test_mismo_dia_inicio_y_fin_incluye_reservas(self, client, admin_token):
        _make_booking(client, "2027-07-15T09:00:00")
        _make_booking(client, "2027-07-15T17:00:00")

        resp = _export(client, admin_token, "2027-07-15", "2027-07-15")
        assert resp.status_code == 200
        rows = _parse_csv(resp.text)
        assert len(rows) == 2

    # ── Content-Type y Content-Disposition ───────────────────────────────────

    def test_content_type_es_csv(self, client, admin_token):
        resp = _export(client, admin_token, "2027-01-01", "2027-01-31")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")

    def test_content_disposition_tiene_nombre_correcto(self, client, admin_token):
        resp = _export(client, admin_token, "2027-03-01", "2027-03-31")
        assert resp.status_code == 200
        cd = resp.headers.get("content-disposition", "")
        assert "attachment" in cd
        assert "reservas_2027-03-01_2027-03-31.csv" in cd
