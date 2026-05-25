"""
Tests unitarios del repositorio SQLAlchemy de reservas.

Verifica que delete() fija deleted_at Y cambia estado a "cancelada",
garantizando consistencia semántica en el registro histórico.
"""

from datetime import datetime

import pytest

from app.infrastructure.persistence.orm.booking import BookingORM
from app.infrastructure.persistence.repositories.booking import SQLAlchemyBookingRepository


def _crear_booking_orm(db_session) -> BookingORM:
    """Helper: inserta un BookingORM en estado 'pendiente' y devuelve su instancia."""
    orm = BookingORM(
        nombre_cliente="Cliente Test",
        telefono="600000000",
        servicio_id=1,
        servicio_nombre="Corte Clásico",
        fecha_hora=datetime(2030, 12, 1, 10, 0),
        barbero="Cualquier barbero",
        estado="pendiente",
    )
    db_session.add(orm)
    db_session.commit()
    db_session.refresh(orm)
    return orm


@pytest.mark.unit
def test_delete_fija_deleted_at(db_session):
    """delete() debe marcar deleted_at para implementar el soft-delete."""
    orm = _crear_booking_orm(db_session)
    repo = SQLAlchemyBookingRepository(db_session)
    repo.delete(orm.id)

    # Consulta directa sin _active() para inspeccionar el registro interno
    fila = db_session.query(BookingORM).filter(BookingORM.id == orm.id).first()
    assert fila is not None, "El registro no debe eliminarse físicamente de la BD"
    assert fila.deleted_at is not None, "deleted_at debe quedar fijado tras delete()"


@pytest.mark.unit
def test_delete_marca_estado_cancelada(db_session):
    """delete() debe cambiar el estado a 'cancelada' además de fijar deleted_at."""
    orm = _crear_booking_orm(db_session)
    repo = SQLAlchemyBookingRepository(db_session)
    repo.delete(orm.id)

    fila = db_session.query(BookingORM).filter(BookingORM.id == orm.id).first()
    assert fila.estado == "cancelada", (
        "Un turno eliminado debe quedar con estado='cancelada' "
        "para garantizar consistencia en informes históricos."
    )


@pytest.mark.unit
def test_delete_hace_invisible_al_booking(db_session):
    """Tras delete(), get_by_id() no debe encontrar el registro."""
    orm = _crear_booking_orm(db_session)
    repo = SQLAlchemyBookingRepository(db_session)
    repo.delete(orm.id)

    resultado = repo.get_by_id(orm.id)
    assert resultado is None, "Un booking soft-deleted no debe ser visible con get_by_id()"
