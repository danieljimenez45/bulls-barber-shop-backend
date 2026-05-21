"""Tests unitarios de la entidad Booking."""

from datetime import datetime

import pytest

from app.domain.booking.entity import Booking


def _make_booking(**kwargs) -> Booking:
    defaults = dict(
        nombre_cliente="Juan Pérez",
        telefono="600000001",
        servicio_id=1,
        fecha_hora=datetime(2026, 6, 10, 10, 0),
    )
    defaults.update(kwargs)
    return Booking(**defaults)


class TestBookingEstados:
    def test_estado_inicial_es_pendiente(self):
        b = _make_booking()
        assert b.estado == "pendiente"

    def test_confirmar(self):
        b = _make_booking()
        b.confirmar()
        assert b.estado == "confirmada"

    def test_cancelar(self):
        b = _make_booking()
        b.cancelar()
        assert b.estado == "cancelada"

    def test_completar(self):
        b = _make_booking()
        b.completar()
        assert b.estado == "completada"

    def test_cambiar_estado_valido(self):
        b = _make_booking()
        b.cambiar_estado("confirmada")
        assert b.estado == "confirmada"

    def test_cambiar_estado_invalido_lanza_error(self):
        b = _make_booking()
        with pytest.raises(ValueError, match="no válido"):
            b.cambiar_estado("en_proceso")
