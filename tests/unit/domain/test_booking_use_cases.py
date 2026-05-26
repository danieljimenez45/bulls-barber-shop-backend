"""
Tests unitarios de los casos de uso de Booking.
Los repositorios y notificadores se mockean con pytest-mock.
"""

from datetime import date, datetime

import pytest

from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, SlotOcupado
from app.domain.booking.use_cases import (
    CancelBookingUseCase,
    CreateBookingUseCase,
    ExportBookingsCSVUseCase,
    GetBookingUseCase,
    GetDisponibilidadUseCase,
    ListBookingsUseCase,
    UpdateBookingUseCase,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _booking(id_=1, estado="pendiente") -> Booking:
    return Booking(
        id=id_,
        nombre_cliente="Test Cliente",
        telefono="600000001",
        servicio_id=1,
        fecha_hora=datetime(2025, 7, 1, 11, 0),
        estado=estado,
    )


# ── CreateBookingUseCase ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_crear_reserva_slot_libre_devuelve_booking(mocker):
    repo = mocker.Mock()
    repo.is_slot_available.return_value = True
    repo.create.return_value = _booking()

    uc = CreateBookingUseCase(repo)
    result = uc.execute(_booking(id_=None))

    repo.create.assert_called_once()
    assert result.id == 1


@pytest.mark.unit
def test_crear_reserva_slot_ocupado_lanza_slot_ocupado(mocker):
    repo = mocker.Mock()
    repo.is_slot_available.return_value = False

    uc = CreateBookingUseCase(repo)
    with pytest.raises(SlotOcupado):
        uc.execute(_booking(id_=None))
    repo.create.assert_not_called()


@pytest.mark.unit
def test_crear_reserva_llama_al_notifier(mocker):
    repo = mocker.Mock()
    repo.is_slot_available.return_value = True
    created = _booking()
    repo.create.return_value = created

    notifier = mocker.Mock()
    uc = CreateBookingUseCase(repo, notifier)
    uc.execute(_booking(id_=None))

    notifier.notify_new_booking.assert_called_once_with(created)


@pytest.mark.unit
def test_crear_reserva_sin_notifier_no_falla(mocker):
    repo = mocker.Mock()
    repo.is_slot_available.return_value = True
    repo.create.return_value = _booking()

    uc = CreateBookingUseCase(repo, notifier=None)
    result = uc.execute(_booking(id_=None))
    assert result is not None


# ── GetBookingUseCase ──────────────────────────────────────────────────────────

@pytest.mark.unit
def test_get_booking_existente(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = _booking(id_=5)

    uc = GetBookingUseCase(repo)
    result = uc.execute(5)

    assert result.id == 5
    repo.get_by_id.assert_called_once_with(5)


@pytest.mark.unit
def test_get_booking_no_encontrado_lanza_booking_not_found(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None

    uc = GetBookingUseCase(repo)
    with pytest.raises(BookingNotFound):
        uc.execute(99)


# ── UpdateBookingUseCase ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_update_booking_cambia_estado(mocker):
    original = _booking(id_=1, estado="pendiente")
    updated = _booking(id_=1, estado="confirmada")

    repo = mocker.Mock()
    repo.get_by_id.return_value = original
    repo.update.return_value = updated

    uc = UpdateBookingUseCase(repo)
    result = uc.execute(1, estado="confirmada")

    assert result.estado == "confirmada"
    repo.update.assert_called_once()


@pytest.mark.unit
def test_update_booking_actualiza_notas_y_barbero(mocker):
    original = _booking(id_=1)
    repo = mocker.Mock()
    repo.get_by_id.return_value = original
    repo.update.side_effect = lambda b: b

    result = UpdateBookingUseCase(repo).execute(
        1, notas="Cliente VIP", barbero="Carlos"
    )

    assert result.notas == "Cliente VIP"
    assert result.barbero == "Carlos"
    repo.update.assert_called_once()


@pytest.mark.unit
def test_update_booking_no_encontrado_lanza_booking_not_found(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None

    uc = UpdateBookingUseCase(repo)
    with pytest.raises(BookingNotFound):
        uc.execute(99, estado="confirmada")


# ── CancelBookingUseCase ───────────────────────────────────────────────────────

@pytest.mark.unit
def test_cancel_booking_llama_repo_delete(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = _booking(id_=3)

    uc = CancelBookingUseCase(repo)
    uc.execute(3)

    repo.delete.assert_called_once_with(3)


@pytest.mark.unit
def test_cancel_booking_no_encontrado_lanza_booking_not_found(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None

    uc = CancelBookingUseCase(repo)
    with pytest.raises(BookingNotFound):
        uc.execute(99)


# ── ExportBookingsCSVUseCase ───────────────────────────────────────────────────

# ── ListBookingsUseCase ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_listar_reservas_devuelve_items_y_total(mocker):
    repo = mocker.Mock()
    repo.list.return_value = [_booking(id_=1), _booking(id_=2)]
    repo.count.return_value = 2
    uc = ListBookingsUseCase(repo)
    items, total = uc.execute()
    assert len(items) == 2
    assert total == 2


@pytest.mark.unit
def test_listar_reservas_filtra_por_estado(mocker):
    repo = mocker.Mock()
    repo.list.return_value = [_booking(estado="confirmada")]
    repo.count.return_value = 1
    uc = ListBookingsUseCase(repo)
    uc.execute(estado="confirmada")
    repo.list.assert_called_once_with(estado="confirmada", skip=0, limit=None)


# ── GetDisponibilidadUseCase ───────────────────────────────────────────────────

@pytest.mark.unit
def test_disponibilidad_delega_en_repositorio(mocker):
    repo = mocker.Mock()
    slots = [datetime(2030, 6, 10, 10, 0), datetime(2030, 6, 10, 11, 0)]
    repo.get_slots_ocupados.return_value = slots
    uc = GetDisponibilidadUseCase(repo)
    result = uc.execute(date(2030, 6, 10))
    assert result == slots
    repo.get_slots_ocupados.assert_called_once_with(date(2030, 6, 10))


# ── ExportBookingsCSVUseCase ───────────────────────────────────────────────────

@pytest.mark.unit
def test_export_hasta_menor_que_desde_lanza_value_error(mocker):
    repo = mocker.Mock()
    uc = ExportBookingsCSVUseCase(repo)

    with pytest.raises(ValueError):
        uc.execute(desde=date(2025, 7, 10), hasta=date(2025, 7, 1))
    repo.list_by_date_range.assert_not_called()


@pytest.mark.unit
def test_export_rango_valido_delega_al_repo(mocker):
    repo = mocker.Mock()
    repo.list_by_date_range.return_value = [_booking()]

    uc = ExportBookingsCSVUseCase(repo)
    result = uc.execute(desde=date(2025, 7, 1), hasta=date(2025, 7, 31))

    repo.list_by_date_range.assert_called_once_with(date(2025, 7, 1), date(2025, 7, 31))
    assert len(result) == 1
