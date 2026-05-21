from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.domain.stats.entity import ProximaCita, ServicioStat, StatsSnapshot
from app.domain.stats.ports import IStatsRepository
from app.infrastructure.persistence.orm.booking import BookingORM
from app.infrastructure.persistence.orm.service import ServiceORM


class SQLAlchemyStatsRepository(IStatsRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Helpers de rango de fechas ─────────────────────────────────────────────

    @staticmethod
    def _rango_hoy() -> tuple[datetime, datetime]:
        hoy = date.today()
        return (
            datetime.combine(hoy, datetime.min.time()),
            datetime.combine(hoy, datetime.max.time()),
        )

    @staticmethod
    def _rango_semana() -> tuple[datetime, datetime]:
        hoy = date.today()
        lunes = hoy - timedelta(days=hoy.weekday())
        domingo = lunes + timedelta(days=6)
        return (
            datetime.combine(lunes, datetime.min.time()),
            datetime.combine(domingo, datetime.max.time()),
        )

    @staticmethod
    def _rango_mes() -> tuple[datetime, datetime]:
        hoy = date.today()
        inicio = hoy.replace(day=1)
        # Último día del mes: primero del siguiente mes menos un día
        if hoy.month == 12:
            fin = date(hoy.year + 1, 1, 1) - timedelta(days=1)
        else:
            fin = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
        return (
            datetime.combine(inicio, datetime.min.time()),
            datetime.combine(fin, datetime.max.time()),
        )

    # ── Consultas individuales ─────────────────────────────────────────────────

    def _contar_citas(self, inicio: datetime, fin: datetime) -> int:
        return (
            self._session.query(func.count(BookingORM.id))
            .filter(
                BookingORM.fecha_hora >= inicio,
                BookingORM.fecha_hora <= fin,
                BookingORM.estado != "cancelada",
            )
            .scalar()
            or 0
        )

    def _ingresos_estimados(self, inicio: datetime, fin: datetime) -> float:
        """Suma los precios de los servicios vinculados a citas confirmadas o
        completadas en el rango dado. Usa LEFT JOIN para no perder citas cuyo
        servicio haya sido eliminado (en ese caso suma 0)."""
        result = (
            self._session.query(func.coalesce(func.sum(ServiceORM.precio), 0.0))
            .select_from(BookingORM)
            .join(ServiceORM, BookingORM.servicio_id == ServiceORM.id, isouter=True)
            .filter(
                BookingORM.estado.in_(["confirmada", "completada"]),
                BookingORM.fecha_hora >= inicio,
                BookingORM.fecha_hora <= fin,
            )
            .scalar()
        )
        return float(result or 0.0)

    def _servicios_mas_solicitados(self, limit: int = 5) -> list[ServicioStat]:
        rows = (
            self._session.query(
                BookingORM.servicio_id,
                BookingORM.servicio_nombre,
                func.count(BookingORM.id).label("total"),
            )
            .filter(BookingORM.estado != "cancelada")
            .group_by(BookingORM.servicio_id, BookingORM.servicio_nombre)
            .order_by(desc("total"))
            .limit(limit)
            .all()
        )
        return [
            ServicioStat(servicio_id=r.servicio_id, nombre=r.servicio_nombre, total=r.total)
            for r in rows
        ]

    def _distribucion_por_estado(self) -> dict[str, int]:
        rows = (
            self._session.query(
                BookingORM.estado,
                func.count(BookingORM.id).label("total"),
            )
            .group_by(BookingORM.estado)
            .all()
        )
        # Garantizar que todos los estados conocidos aparecen aunque sean 0
        base = {e: 0 for e in ("pendiente", "confirmada", "cancelada", "completada")}
        for estado, total in rows:
            if estado:
                base[estado] = total
        return base

    def _proxima_cita(self) -> Optional[ProximaCita]:
        ahora = datetime.now()
        orm = (
            self._session.query(BookingORM)
            .filter(
                BookingORM.fecha_hora > ahora,
                BookingORM.estado.in_(["pendiente", "confirmada"]),
            )
            .order_by(BookingORM.fecha_hora)
            .first()
        )
        if not orm:
            return None
        return ProximaCita(
            id=orm.id,
            nombre_cliente=orm.nombre_cliente,
            telefono=orm.telefono,
            fecha_hora=orm.fecha_hora,
            servicio_nombre=orm.servicio_nombre,
            estado=orm.estado,
        )

    # ── Puerto ────────────────────────────────────────────────────────────────

    def get_snapshot(self) -> StatsSnapshot:
        inicio_hoy, fin_hoy = self._rango_hoy()
        inicio_semana, fin_semana = self._rango_semana()
        inicio_mes, fin_mes = self._rango_mes()

        return StatsSnapshot(
            citas_hoy=self._contar_citas(inicio_hoy, fin_hoy),
            citas_semana=self._contar_citas(inicio_semana, fin_semana),
            citas_mes=self._contar_citas(inicio_mes, fin_mes),
            ingresos_estimados_semana=self._ingresos_estimados(inicio_semana, fin_semana),
            ingresos_estimados_mes=self._ingresos_estimados(inicio_mes, fin_mes),
            servicios_mas_solicitados=self._servicios_mas_solicitados(),
            distribucion_por_estado=self._distribucion_por_estado(),
            proxima_cita=self._proxima_cita(),
        )
