"""Tests de integración del repositorio de estadísticas."""

from datetime import datetime, timedelta

import pytest

from app.domain.booking.entity import Booking
from app.infrastructure.persistence.orm.service import ServiceORM
from app.infrastructure.persistence.repositories.booking import SQLAlchemyBookingRepository
from app.infrastructure.persistence.repositories.stats import SQLAlchemyStatsRepository


@pytest.mark.integration
def test_get_snapshot_con_datos(db_session):
    # Servicio con precio para ingresos estimados
    svc = ServiceORM(
        nombre="Corte",
        precio=20.0,
        duracion_minutos=30,
        categoria="corte",
        activo=True,
    )
    db_session.add(svc)
    db_session.commit()
    db_session.refresh(svc)

    booking_repo = SQLAlchemyBookingRepository(db_session)
    manana = datetime.now() + timedelta(days=1)
    booking_repo.create(
        Booking(
            nombre_cliente="Cliente",
            telefono="600000000",
            servicio_id=svc.id,
            servicio_nombre="Corte",
            fecha_hora=manana.replace(hour=10, minute=0, second=0, microsecond=0),
            estado="confirmada",
        )
    )

    snapshot = SQLAlchemyStatsRepository(db_session).get_snapshot()

    assert snapshot.citas_mes >= 1
    assert "pendiente" in snapshot.distribucion_por_estado
    assert snapshot.proxima_cita is not None
    assert snapshot.proxima_cita.nombre_cliente == "Cliente"


@pytest.mark.integration
def test_stats_excluye_soft_deleted_de_conteos(db_session):
    svc = ServiceORM(
        nombre="Corte",
        precio=15.0,
        duracion_minutos=30,
        categoria="corte",
        activo=True,
    )
    db_session.add(svc)
    db_session.commit()
    db_session.refresh(svc)

    booking_repo = SQLAlchemyBookingRepository(db_session)
    manana = datetime.now() + timedelta(days=1)
    slot = manana.replace(hour=11, minute=0, second=0, microsecond=0)
    activa = booking_repo.create(
        Booking(
            nombre_cliente="Activa",
            telefono="600000001",
            servicio_id=svc.id,
            servicio_nombre="Corte",
            fecha_hora=slot,
            estado="confirmada",
        )
    )
    eliminada = booking_repo.create(
        Booking(
            nombre_cliente="Eliminada",
            telefono="600000002",
            servicio_id=svc.id,
            servicio_nombre="Corte",
            fecha_hora=slot.replace(hour=12),
            estado="confirmada",
        )
    )
    booking_repo.delete(eliminada.id)

    snapshot = SQLAlchemyStatsRepository(db_session).get_snapshot()
    assert snapshot.citas_mes == 1
    assert activa.id is not None


@pytest.mark.integration
def test_get_snapshot_vacio(db_session):
    snapshot = SQLAlchemyStatsRepository(db_session).get_snapshot()
    assert snapshot.citas_hoy == 0
    assert snapshot.proxima_cita is None
