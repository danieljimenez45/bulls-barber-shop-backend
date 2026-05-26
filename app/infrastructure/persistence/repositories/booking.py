"""
Repositorio SQLAlchemy para el dominio de reservas.

Todas las queries filtran registros con deleted_at IS NULL para implementar
soft-delete sin pérdida de datos históricos.

delete() fija deleted_at = now(UTC) Y cambia estado a "cancelada", garantizando
consistencia semántica: un turno eliminado queda también marcado como cancelado,
lo que facilita auditorías e informes históricos que consulten la columna estado.
"""

from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, IBookingRepository, SlotOcupado
from app.domain.booking.rules import BOOKING_ACTIVE_STATES
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
            deleted_at=orm.deleted_at,
        )

    # ── Helper: filtro base que excluye registros soft-deleted ────────────────

    def _active(self, query):
        """Aplica el filtro de soft-delete a cualquier query."""
        return query.filter(BookingORM.deleted_at.is_(None))

    # ── Puerto ────────────────────────────────────────────────────────────────

    def create(self, booking: Booking) -> Booking:
        if not self.is_slot_available(booking.fecha_hora):
            raise SlotOcupado(
                f"El horario {booking.fecha_hora.strftime('%d/%m/%Y a las %H:%M')} "
                "ya está reservado. Por favor elige otro horario."
            )
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
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise SlotOcupado(
                "El horario seleccionado ya no está disponible. Por favor elige otro."
            ) from exc
        self._session.refresh(orm)
        return self._to_entity(orm)

    def get_by_id(self, booking_id: int) -> Optional[Booking]:
        orm = (
            self._active(self._session.query(BookingORM))
            .filter(BookingORM.id == booking_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def list(
        self,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Booking]:
        query = self._active(self._session.query(BookingORM))
        if estado:
            query = query.filter(BookingORM.estado == estado)
        query = query.order_by(BookingORM.fecha_hora.desc()).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return [self._to_entity(o) for o in query.all()]

    def count(self, estado: Optional[str] = None) -> int:
        query = self._active(self._session.query(func.count(BookingORM.id)))
        if estado:
            query = query.filter(BookingORM.estado == estado)
        return query.scalar() or 0

    def update(self, booking: Booking) -> Booking:
        orm = (
            self._active(self._session.query(BookingORM))
            .filter(BookingORM.id == booking.id)
            .first()
        )
        if not orm:
            raise BookingNotFound(f"Reserva {booking.id} no encontrada")
        orm.estado  = booking.estado
        orm.notas   = booking.notas
        orm.barbero = booking.barbero
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def delete(self, booking_id: int) -> None:
        """
        Soft-delete: fija deleted_at al instante actual Y cambia estado a "cancelada".

        Fijar deleted_at hace que _active() excluya el registro de todas las
        consultas normales. Cambiar estado a "cancelada" añade consistencia
        semántica: si en el futuro se consulta la tabla sin el filtro deleted_at
        (p.ej. en un informe histórico), el registro refleja correctamente que
        el turno fue cancelado y no simplemente eliminado por error.
        """
        orm = (
            self._active(self._session.query(BookingORM))
            .filter(BookingORM.id == booking_id)
            .first()
        )
        if not orm:
            raise BookingNotFound(f"Reserva {booking_id} no encontrada")
        orm.estado = "cancelada"
        orm.deleted_at = datetime.now(timezone.utc)
        self._session.commit()

    def is_slot_available(self, fecha_hora: datetime) -> bool:
        """True si no hay cita pendiente/confirmada activa en ese instante."""
        count = (
            self._active(self._session.query(func.count(BookingORM.id)))
            .filter(
                BookingORM.fecha_hora == fecha_hora,
                BookingORM.estado.in_(tuple(BOOKING_ACTIVE_STATES)),
            )
            .scalar()
            or 0
        )
        return count == 0

    def get_slots_ocupados(self, fecha: date) -> list[datetime]:
        """Devuelve horas con reserva pendiente o confirmada en la fecha dada."""
        inicio = datetime.combine(fecha, datetime.min.time())
        fin = datetime.combine(fecha, datetime.max.time())
        rows = (
            self._active(self._session.query(BookingORM.fecha_hora))
            .filter(
                BookingORM.fecha_hora >= inicio,
                BookingORM.fecha_hora <= fin,
                BookingORM.estado.in_(tuple(BOOKING_ACTIVE_STATES)),
            )
            .all()
        )
        return [r.fecha_hora for r in rows]

    def list_by_date_range(self, desde: date, hasta: date) -> List[Booking]:
        """
        Devuelve reservas activas (no eliminadas) cuya fecha_hora cae en
        [desde 00:00, hasta 23:59:59], ordenadas por fecha_hora ascendente.
        """
        inicio = datetime.combine(desde, datetime.min.time())
        fin    = datetime.combine(hasta, datetime.max.time())
        rows = (
            self._active(self._session.query(BookingORM))
            .filter(
                BookingORM.fecha_hora >= inicio,
                BookingORM.fecha_hora <= fin,
            )
            .order_by(BookingORM.fecha_hora)
            .all()
        )
        return [self._to_entity(o) for o in rows]
