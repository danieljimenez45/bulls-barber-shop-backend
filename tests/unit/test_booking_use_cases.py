"""Tests unitarios de los casos de uso de reservas (mocks de repositorio)."""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, SlotOcupado
from app.domain.booking.use_cases import (
    CancelBookingUseCase,
    CreateBookingUseCase,
    GetBookingUseCase,
    GetDisponibilidadUseCase,
    ListBookingsUseCase,
    UpdateBookingUseCase,
)


def _booking(id=1, estado="pendiente") -> Booking:
    return Booking(
        id=id,
        nombre_cliente="Juan",
        telefono="600000001",
        servicio_id=1,
        fecha_hora=datetime(2026, 6, 10, 10, 0),
        estado=estado,
    )


# ── CreateBookingUseCase ───────────────────────────────────────────────────────

class TestCreateBookingUseCase:
    def test_crea_si_slot_libre(self):
        repo = MagicMock()
        repo.is_slot_available.return_value = True
        repo.create.return_value = _booking()
        uc = CreateBookingUseCase(repo)
        result = uc.execute(_booking(id=None))
        assert result.id == 1
        repo.create.assert_called_once()

    def test_lanza_slot_ocupado_si_no_disponible(self):
        repo = MagicMock()
        repo.is_slot_available.return_value = False
        uc = CreateBookingUseCase(repo)
        with pytest.raises(SlotOcupado):
            uc.execute(_booking(id=None))
        repo.create.assert_not_called()

    def test_llama_notifier_si_configurado(self):
        repo = MagicMock()
        repo.is_slot_available.return_value = True
        repo.create.return_value = _booking()
        notifier = MagicMock()
        uc = CreateBookingUseCase(repo, notifier)
        uc.execute(_booking(id=None))
        notifier.notify_new_booking.assert_called_once()

    def test_no_llama_notifier_si_no_configurado(self):
        repo = MagicMock()
        repo.is_slot_available.return_value = True
        repo.create.return_value = _booking()
        uc = CreateBookingUseCase(repo, notifier=None)
        uc.execute(_booking(id=None))  # no debe lanzar AttributeError


# ── GetBookingUseCase ─────────────────────────────────────────────────────────

class TestGetBookingUseCase:
    def test_devuelve_booking(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _booking()
        uc = GetBookingUseCase(repo)
        result = uc.execute(1)
        assert result.id == 1

    def test_lanza_not_found_si_no_existe(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        uc = GetBookingUseCase(repo)
        with pytest.raises(BookingNotFound):
            uc.execute(999)


# ── ListBookingsUseCase ───────────────────────────────────────────────────────

class TestListBookingsUseCase:
    def test_devuelve_items_y_total(self):
        repo = MagicMock()
        repo.list.return_value = [_booking(1), _booking(2)]
        repo.count.return_value = 2
        uc = ListBookingsUseCase(repo)
        items, total = uc.execute()
        assert len(items) == 2
        assert total == 2

    def test_filtra_por_estado(self):
        repo = MagicMock()
        repo.list.return_value = [_booking(estado="confirmada")]
        repo.count.return_value = 1
        uc = ListBookingsUseCase(repo)
        uc.execute(estado="confirmada")
        repo.list.assert_called_once_with(estado="confirmada", skip=0, limit=None)


# ── UpdateBookingUseCase ──────────────────────────────────────────────────────

class TestUpdateBookingUseCase:
    def test_actualiza_estado(self):
        b = _booking()
        repo = MagicMock()
        repo.get_by_id.return_value = b
        repo.update.return_value = b
        uc = UpdateBookingUseCase(repo)
        uc.execute(1, estado="confirmada")
        assert b.estado == "confirmada"
        repo.update.assert_called_once()

    def test_lanza_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        uc = UpdateBookingUseCase(repo)
        with pytest.raises(BookingNotFound):
            uc.execute(999, estado="confirmada")

    def test_lanza_value_error_estado_invalido(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _booking()
        uc = UpdateBookingUseCase(repo)
        with pytest.raises(ValueError):
            uc.execute(1, estado="en_vuelo")


# ── CancelBookingUseCase ──────────────────────────────────────────────────────

class TestCancelBookingUseCase:
    def test_cancela_correctamente(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _booking()
        uc = CancelBookingUseCase(repo)
        uc.execute(1)
        repo.delete.assert_called_once_with(1)

    def test_lanza_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        uc = CancelBookingUseCase(repo)
        with pytest.raises(BookingNotFound):
            uc.execute(999)


# ── GetDisponibilidadUseCase ──────────────────────────────────────────────────

class TestGetDisponibilidadUseCase:
    def test_delega_en_repositorio(self):
        repo = MagicMock()
        slots = [datetime(2026, 6, 10, 10, 0), datetime(2026, 6, 10, 11, 0)]
        repo.get_slots_ocupados.return_value = slots
        uc = GetDisponibilidadUseCase(repo)
        result = uc.execute(date(2026, 6, 10))
        assert result == slots
        repo.get_slots_ocupados.assert_called_once_with(date(2026, 6, 10))
