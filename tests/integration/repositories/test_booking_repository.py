"""
Tests de integración del repositorio SQLAlchemy de Booking.
Usa SQLite en memoria via la fixture db_session de conftest.
"""

from datetime import date, datetime

import pytest

from app.domain.booking.ports import BookingNotFound
from app.infrastructure.persistence.orm.booking import BookingORM
from app.infrastructure.persistence.repositories.booking import SQLAlchemyBookingRepository
from tests.helpers import domain_booking

pytestmark = pytest.mark.usefixtures("seed_booking_service")


@pytest.mark.integration
def test_create_devuelve_entidad_con_id(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    created = repo.create(domain_booking())
    assert created.id is not None
    assert created.nombre_cliente == "Cliente Test"


@pytest.mark.integration
def test_get_by_id_existente(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    created = repo.create(domain_booking())
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


@pytest.mark.integration
def test_get_by_id_no_existente_devuelve_none(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    assert repo.get_by_id(9999) is None


@pytest.mark.integration
def test_list_sin_filtros(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 11, 0)))
    items = repo.list()
    assert len(items) == 2


@pytest.mark.integration
def test_list_filtrado_por_estado(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    b1 = repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0), estado="pendiente"))
    b2 = repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 11, 0), estado="pendiente"))
    # Confirmar b2
    b2.estado = "confirmada"
    repo.update(b2)

    pendientes = repo.list(estado="pendiente")
    assert len(pendientes) == 1
    assert pendientes[0].id == b1.id


@pytest.mark.integration
def test_list_respeta_skip_y_limit(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    for i in range(5):
        repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10 + i, 0)))
    page = repo.list(skip=2, limit=2)
    assert len(page) == 2


@pytest.mark.integration
def test_count_total(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 11, 0)))
    assert repo.count() == 2


@pytest.mark.integration
def test_count_por_estado(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    b = repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 11, 0)))
    # Confirmar el primero
    b.estado = "confirmada"
    repo.update(b)
    assert repo.count(estado="confirmada") == 1
    assert repo.count(estado="pendiente") == 1


@pytest.mark.integration
def test_update_persiste_cambios(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    created = repo.create(domain_booking())
    created.estado = "confirmada"
    created.notas = "Nota actualizada"
    updated = repo.update(created)
    assert updated.estado == "confirmada"
    assert updated.notas == "Nota actualizada"


@pytest.mark.integration
def test_delete_softdelete_invisible_para_get(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    created = repo.create(domain_booking())
    repo.delete(created.id)
    assert repo.get_by_id(created.id) is None


@pytest.mark.integration
def test_delete_fija_deleted_at_y_estado_cancelada(db_session):
    """Soft-delete: deleted_at + estado cancelada en el registro ORM."""
    repo = SQLAlchemyBookingRepository(db_session)
    created = repo.create(domain_booking())
    repo.delete(created.id)

    fila = db_session.query(BookingORM).filter(BookingORM.id == created.id).first()
    assert fila is not None
    assert fila.deleted_at is not None
    assert fila.estado == "cancelada"


@pytest.mark.integration
def test_update_reserva_inexistente_lanza_booking_not_found(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    ghost = domain_booking()
    ghost.id = 9999
    with pytest.raises(BookingNotFound):
        repo.update(ghost)


@pytest.mark.integration
def test_delete_softdelete_no_cuenta_en_count(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    b = repo.create(domain_booking())
    repo.delete(b.id)
    assert repo.count() == 0


@pytest.mark.integration
def test_delete_registro_no_existente_lanza_booking_not_found(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    with pytest.raises(BookingNotFound):
        repo.delete(9999)


@pytest.mark.integration
def test_is_slot_available_libre(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    assert repo.is_slot_available(datetime(2025, 8, 15, 10, 0)) is True


@pytest.mark.integration
def test_is_slot_available_ocupado(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    assert repo.is_slot_available(datetime(2025, 8, 15, 10, 0)) is False


@pytest.mark.integration
def test_is_slot_available_completada_cuenta_como_libre(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    b = repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    b.estado = "completada"
    repo.update(b)
    assert repo.is_slot_available(datetime(2025, 8, 15, 10, 0)) is True


@pytest.mark.integration
def test_create_integrity_error_lanza_slot_ocupado(db_session, mocker):
    from sqlalchemy.exc import IntegrityError

    repo = SQLAlchemyBookingRepository(db_session)
    mocker.patch.object(repo, "is_slot_available", return_value=True)
    mocker.patch.object(
        db_session,
        "commit",
        side_effect=IntegrityError("stmt", {}, Exception("unique")),
    )

    with pytest.raises(Exception) as exc_info:
        repo.create(domain_booking())
    from app.domain.booking.ports import SlotOcupado

    assert isinstance(exc_info.value, SlotOcupado)


@pytest.mark.integration
def test_is_slot_available_cancelada_cuenta_como_libre(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    b = repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    b.estado = "cancelada"
    repo.update(b)
    # Slot cancelado → debe estar libre
    assert repo.is_slot_available(datetime(2025, 8, 15, 10, 0)) is True


@pytest.mark.integration
def test_get_slots_ocupados_filtra_por_fecha(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 11, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 16, 10, 0)))  # otro día

    slots = repo.get_slots_ocupados(date(2025, 8, 15))
    assert len(slots) == 2


@pytest.mark.integration
def test_get_slots_ocupados_excluye_canceladas(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    b = repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    b.estado = "cancelada"
    repo.update(b)

    slots = repo.get_slots_ocupados(date(2025, 8, 15))
    assert len(slots) == 0


@pytest.mark.integration
def test_list_by_date_range_filtra_correctamente(db_session):
    repo = SQLAlchemyBookingRepository(db_session)
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 1, 10, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 8, 15, 10, 0)))
    repo.create(domain_booking(fecha_hora=datetime(2025, 9, 1, 10, 0)))

    result = repo.list_by_date_range(date(2025, 8, 1), date(2025, 8, 31))
    assert len(result) == 2
