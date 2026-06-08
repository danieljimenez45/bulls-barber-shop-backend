"""
Repositorio SQLAlchemy para el dominio de reservas.

Todas las queries filtran registros con deleted_at IS NULL para implementar
soft-delete sin pérdida de datos históricos.

delete() fija deleted_at = now(UTC) Y cambia estado a "cancelada", garantizando
consistencia semántica: un turno eliminado queda también marcado como cancelado,
lo que facilita auditorías e informes históricos que consulten la columna estado.

Lógica de solapamiento (grid :00/:30):
  Una nueva reserva en [T, T+D_new) solapa con una existente en [S, S+D_s) si:
      S < T + D_new  AND  T < S + D_s
  Esto garantiza que un servicio de 60 min reservado a las 10:00 bloquea
  también el slot de las 10:30.
"""

from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, IBookingRepository, SlotOcupado
from app.domain.booking.rules import BOOKING_ACTIVE_STATES, SLOT_INTERVAL_MINUTES
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
            duracion_minutos=orm.duracion_minutos,
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
        if not self.is_slot_available(booking.fecha_hora, booking.duracion_minutos):
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
            duracion_minutos=booking.duracion_minutos,
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

    def is_slot_available(self, fecha_hora: datetime, duracion_minutos: int = 30) -> bool:
        """True si [fecha_hora, fecha_hora+duracion_minutos) no solapa con ninguna
        cita activa existente.

        Condición de solapamiento entre [T, T+D_new) y [S, S+D_s):
            S < T + D_new  AND  T < S + D_s

        SQLite no soporta aritmética de columnas con timedelta, así que el primer
        filtro (S < T+D_new) se aplica en SQL y la condición completa se valida
        en Python con el conjunto reducido de candidatos.
        """
        # Normalizar a naive para comparar con los valores almacenados en SQLite.
        fh = fecha_hora.replace(tzinfo=None) if fecha_hora.tzinfo else fecha_hora
        nueva_fin = fh + timedelta(minutes=duracion_minutos)

        # Candidatos: reservas activas que empiezan antes del fin de la nueva reserva
        # y dentro de una ventana razonable (ningún servicio dura más de 4 h).
        window_start = fh - timedelta(hours=4)
        candidates = (
            self._active(
                self._session.query(BookingORM.fecha_hora, BookingORM.duracion_minutos)
            )
            .filter(
                BookingORM.estado.in_(tuple(BOOKING_ACTIVE_STATES)),
                BookingORM.fecha_hora >= window_start,
                BookingORM.fecha_hora < nueva_fin,
            )
            .all()
        )

        for s, d_s in candidates:
            s_naive = s.replace(tzinfo=None) if s.tzinfo else s
            existing_fin = s_naive + timedelta(minutes=d_s)
            # Overlap: S < T+D_new  AND  T < S+D_s
            if s_naive < nueva_fin and fh < existing_fin:
                return False
        return True

    def get_slots_ocupados(self, fecha: date) -> list[datetime]:
        """Devuelve todos los slots de 30 min bloqueados en la fecha dada.

        Para cada reserva activa, expande sus slots ocupados según su duración:
        una reserva de 60 min a las 10:00 bloquea {10:00, 10:30}.
        """
        inicio = datetime.combine(fecha, datetime.min.time())
        fin    = datetime.combine(fecha, datetime.max.time())
        rows = (
            self._active(
                self._session.query(BookingORM.fecha_hora, BookingORM.duracion_minutos)
            )
            .filter(
                BookingORM.fecha_hora >= inicio,
                BookingORM.fecha_hora <= fin,
                BookingORM.estado.in_(tuple(BOOKING_ACTIVE_STATES)),
            )
            .all()
        )
        slots: set[datetime] = set()
        interval = timedelta(minutes=SLOT_INTERVAL_MINUTES)
        for fh, dur in rows:
            n_slots = max(1, -(-dur // SLOT_INTERVAL_MINUTES))  # ceil division
            for i in range(n_slots):
                slots.add(fh + i * interval)
        return sorted(slots)

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
