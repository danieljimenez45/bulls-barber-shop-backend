from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, IBookingRepository
from app.infrastructure.persistence.orm.booking import BookingORM


class SQLAlchemyBookingRepository(IBookingRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Traducción ORM → Entidad ──────────────────────────────────────────────

    @staticmethod
    def _to_entity(orm: BookingORM) -> Booking:
        return Booking(
            id=orm.id,
            nombre_cliente=orm.nombre_cliente,
            telefono=orm.telefono,
            email=orm.email,
            servicio_id=orm.servicio_id,
            servicio_nombre=orm.servicio_nombre,
            fecha_hora=orm.fecha_hora,
            barbero=orm.barbero,
            notas=orm.notas,
            estado=orm.estado,
            created_at=orm.created_at,
        )

    # ── Puerto ────────────────────────────────────────────────────────────────

    def create(self, booking: Booking) -> Booking:
        orm = BookingORM(
            nombre_cliente=booking.nombre_cliente,
            telefono=booking.telefono,
            email=booking.email,
            servicio_id=booking.servicio_id,
            servicio_nombre=booking.servicio_nombre,
            fecha_hora=booking.fecha_hora,
            barbero=booking.barbero,
            notas=booking.notas,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        orm = (
            self._session.query(BookingORM)
            .filter(BookingORM.id == booking_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def list(self, estado: Optional[str] = None) -> List[Booking]:
        query = self._session.query(BookingORM)
        if estado:
            query = query.filter(BookingORM.estado == estado)
        return [
            self._to_entity(o)
            for o in query.order_by(BookingORM.fecha_hora).all()
        ]

    def update(self, booking: Booking) -> Booking:
        orm = (
            self._session.query(BookingORM)
            .filter(BookingORM.id == booking.id)
            .first()
        )
        if not orm:
            raise BookingNotFound(f"Reserva {booking.id} no encontrada")
        orm.estado = booking.estado
        orm.notas = booking.notas
        orm.barbero = booking.barbero
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def delete(self, booking_id: int) -> None:
        orm = (
            self._session.query(BookingORM)
            .filter(BookingORM.id == booking_id)
            .first()
        )
        if not orm:
            raise BookingNotFound(f"Reserva {booking_id} no encontrada")
        orm.estado = "cancelada"
        self._session.commit()

    def is_slot_available(self, fecha_hora: datetime) -> bool:
        """True si no hay ninguna cita activa (no cancelada) en ese instante exacto."""
        count = (
            self._session.query(func.count(BookingORM.id))
            .filter(
                BookingORM.fecha_hora == fecha_hora,
                BookingORM.estado != "cancelada",
            )
            .scalar()
            or 0
        )
        return count == 0

    def get_slots_ocupados(self, fecha: date) -> list[datetime]:
        """Devuelve las horas ocupadas (no canceladas) en la fecha dada."""
        inicio = datetime.combine(fecha, datetime.min.time())
        fin = datetime.combine(fecha, datetime.max.time())
        rows = (
            self._session.query(BookingORM.fecha_hora)
            .filter(
                BookingORM.fecha_hora >= inicio,
                BookingORM.fecha_hora <= fin,
                BookingORM.estado != "cancelada",
            )
            .all()
        )
        return [r.fecha_hora for r in rows]
