"""Tests unitarios de los schemas Pydantic de entrada.

Verifica que BookingCreate y ReviewCreate:
  - Aceptan payloads válidos.
  - Rechazan campos extra (extra="forbid" → 422).
  - Limpian espacios en strings (str_strip_whitespace).
  - Aplican las reglas de negocio específicas de cada campo.
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

from app.api.schemas.booking import BookingCreate, BookingUpdate
from app.api.schemas.review import ReviewCreate

# ── Helpers ───────────────────────────────────────────────────────────────────

def future_dt(hours: int = 2) -> datetime:
    """Devuelve un datetime UTC con timezone en el futuro."""
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def valid_booking(**overrides) -> dict:
    base = {
        "nombre_cliente": "Juan García",
        "telefono": "612345678",
        "email": "juan@example.com",
        "servicio_id": 1,
        "fecha_hora": future_dt().isoformat(),
    }
    return {**base, **overrides}


def valid_review(**overrides) -> dict:
    base = {
        "nombre": "Carlos",
        "valoracion": 5,
        "comentario": "Muy buen servicio y trato excelente.",
    }
    return {**base, **overrides}


# ── BookingCreate — casos válidos ─────────────────────────────────────────────

class TestBookingCreateValidos:
    def test_payload_minimo_valido(self):
        data = valid_booking()
        del data["email"]
        b = BookingCreate(**data)
        assert b.nombre_cliente == "Juan García"

    def test_payload_completo_valido(self):
        b = BookingCreate(**valid_booking(notas="Degradado bajo", barbero="Jonathan"))
        assert b.barbero == "Jonathan"
        assert b.notas == "Degradado bajo"

    def test_telefono_movil_6(self):
        b = BookingCreate(**valid_booking(telefono="612345678"))
        assert b.telefono == "612345678"

    def test_telefono_movil_7(self):
        b = BookingCreate(**valid_booking(telefono="712345678"))
        assert b.telefono == "712345678"

    def test_telefono_fijo_8(self):
        b = BookingCreate(**valid_booking(telefono="812345678"))
        assert b.telefono == "812345678"

    def test_telefono_fijo_9(self):
        b = BookingCreate(**valid_booking(telefono="912345678"))
        assert b.telefono == "912345678"

    def test_telefono_con_prefijo_34(self):
        b = BookingCreate(**valid_booking(telefono="+34612345678"))
        assert b.telefono == "+34612345678"

    def test_telefono_con_prefijo_0034(self):
        b = BookingCreate(**valid_booking(telefono="0034612345678"))
        assert b.telefono == "0034612345678"

    def test_nombre_con_espacios_extremos_se_limpia(self):
        b = BookingCreate(**valid_booking(nombre_cliente="  Juan García  "))
        assert b.nombre_cliente == "Juan García"

    def test_notas_con_espacios_extremos_se_limpian(self):
        b = BookingCreate(**valid_booking(notas="  texto  "))
        assert b.notas == "texto"

    def test_email_es_opcional(self):
        data = valid_booking()
        data.pop("email", None)
        b = BookingCreate(**data)
        assert b.email is None


# ── BookingCreate — campos inválidos ──────────────────────────────────────────

class TestBookingCreateInvalidos:
    def test_campo_extra_rechazado(self):
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(**valid_booking(admin=True))
        assert "extra_forbidden" in str(exc_info.value)

    def test_nombre_demasiado_corto(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(nombre_cliente="A"))

    def test_nombre_vacio(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(nombre_cliente=""))

    def test_nombre_solo_espacios_falla_min_length(self):
        # str_strip_whitespace lo convierte en "" → falla min_length=2
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(nombre_cliente="   "))

    def test_telefono_empieza_por_5_invalido(self):
        with pytest.raises(ValidationError) as exc_info:
            BookingCreate(**valid_booking(telefono="512345678"))
        assert "teléfono" in str(exc_info.value).lower()

    def test_telefono_demasiado_corto(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(telefono="61234"))

    def test_telefono_demasiado_largo(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(telefono="6123456789"))

    def test_telefono_con_letras_invalido(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(telefono="6abc45678"))

    def test_servicio_id_cero_invalido(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(servicio_id=0))

    def test_servicio_id_negativo_invalido(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(servicio_id=-1))

    def test_fecha_en_pasado_invalida(self):
        pasado = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(fecha_hora=pasado))

    def test_email_invalido(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(email="no-es-un-email"))

    def test_notas_demasiado_largas(self):
        with pytest.raises(ValidationError):
            BookingCreate(**valid_booking(notas="x" * 501))


# ── BookingUpdate — extra="forbid" ────────────────────────────────────────────

class TestBookingUpdate:
    def test_campo_extra_rechazado(self):
        with pytest.raises(ValidationError) as exc_info:
            BookingUpdate(estado="confirmada", campo_raro="hack")
        assert "extra_forbidden" in str(exc_info.value)

    def test_estado_valido(self):
        u = BookingUpdate(estado="confirmada")
        assert u.estado == "confirmada"

    def test_estado_cancelada_rechazado(self):
        with pytest.raises(ValidationError):
            BookingUpdate(estado="cancelada")

    def test_payload_vacio_valido(self):
        u = BookingUpdate()
        assert u.estado is None
        assert u.notas is None

    def test_notas_con_espacios_se_limpian(self):
        u = BookingUpdate(notas="  texto  ")
        assert u.notas == "texto"


# ── ReviewCreate — casos válidos ──────────────────────────────────────────────

class TestReviewCreateValidos:
    def test_payload_completo_valido(self):
        r = ReviewCreate(**valid_review())
        assert r.nombre == "Carlos"
        assert r.valoracion == 5

    def test_sin_comentario_valido(self):
        data = valid_review()
        del data["comentario"]
        r = ReviewCreate(**data)
        assert r.comentario is None

    def test_comentario_vacio_se_convierte_a_none(self):
        r = ReviewCreate(**valid_review(comentario=""))
        assert r.comentario is None

    def test_comentario_solo_espacios_se_convierte_a_none(self):
        r = ReviewCreate(**valid_review(comentario="     "))
        assert r.comentario is None

    def test_nombre_con_espacios_extremos_se_limpia(self):
        r = ReviewCreate(**valid_review(nombre="  Carlos  "))
        assert r.nombre == "Carlos"

    def test_valoracion_minima(self):
        r = ReviewCreate(**valid_review(valoracion=1))
        assert r.valoracion == 1

    def test_valoracion_maxima(self):
        r = ReviewCreate(**valid_review(valoracion=5))
        assert r.valoracion == 5


# ── ReviewCreate — campos inválidos ───────────────────────────────────────────

class TestReviewCreateInvalidos:
    def test_campo_extra_rechazado(self):
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(**valid_review(spam_field="hack"))
        assert "extra_forbidden" in str(exc_info.value)

    def test_nombre_demasiado_corto(self):
        with pytest.raises(ValidationError):
            ReviewCreate(**valid_review(nombre="A"))

    def test_nombre_solo_espacios_falla_min_length(self):
        with pytest.raises(ValidationError):
            ReviewCreate(**valid_review(nombre="  "))

    def test_valoracion_cero_invalida(self):
        with pytest.raises(ValidationError):
            ReviewCreate(**valid_review(valoracion=0))

    def test_valoracion_seis_invalida(self):
        with pytest.raises(ValidationError):
            ReviewCreate(**valid_review(valoracion=6))

    def test_comentario_demasiado_corto(self):
        with pytest.raises(ValidationError) as exc_info:
            ReviewCreate(**valid_review(comentario="Bien"))
        assert "10 caracteres" in str(exc_info.value)

    def test_comentario_demasiado_largo(self):
        with pytest.raises(ValidationError):
            ReviewCreate(**valid_review(comentario="x" * 1001))
