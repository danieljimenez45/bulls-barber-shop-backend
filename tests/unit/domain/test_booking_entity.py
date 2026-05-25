"""Tests unitarios de la entidad Booking (dominio puro, sin dependencias externas)."""

from datetime import datetime

import pytest

from app.domain.booking.entity import Booking


def _make_booking(**kwargs) -> Booking:
    defaults = dict(
        nombre_cliente="Juan García",
        telefono="600123456",
        servicio_id=1,
        fecha_hora=datetime(2025, 6, 15, 10, 0),
    )
    defaults.update(kwargs)
    return Booking(**defaults)


# ── Estado inicial ─────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_estado_inicial_es_pendiente():
    b = _make_booking()
    assert b.estado == "pendiente"


@pytest.mark.unit
def test_deleted_at_es_none_por_defecto():
    b = _make_booking()
    assert b.deleted_at is None


# ── Transiciones de estado ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_confirmar_cambia_estado():
    b = _make_booking()
    b.confirmar()
    assert b.estado == "confirmada"


@pytest.mark.unit
def test_cancelar_cambia_estado():
    b = _make_booking()
    b.cancelar()
    assert b.estado == "cancelada"


@pytest.mark.unit
def test_completar_cambia_estado():
    b = _make_booking()
    b.completar()
    assert b.estado == "completada"


@pytest.mark.unit
def test_cambiar_estado_valido():
    b = _make_booking()
    b.cambiar_estado("confirmada")
    assert b.estado == "confirmada"


@pytest.mark.unit
def test_cambiar_estado_invalido_lanza_value_error():
    b = _make_booking()
    with pytest.raises(ValueError, match="no válido"):
        b.cambiar_estado("inexistente")


# ── ESTADOS_VALIDOS ────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_estados_validos_son_cuatro():
    assert len(Booking.ESTADOS_VALIDOS) == 4
    assert Booking.ESTADOS_VALIDOS == {"pendiente", "confirmada", "cancelada", "completada"}
