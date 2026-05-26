"""Reglas de negocio compartidas para reservas."""

from datetime import datetime, timezone

BOOKING_ACTIVE_STATES = frozenset({"pendiente", "confirmada"})


class FechaEnPasado(Exception):
    """La fecha/hora de la reserva no es futura respecto a UTC."""


def assert_future_datetime(fecha_hora: datetime, *, now: datetime | None = None) -> None:
    ref = now or datetime.now(timezone.utc)
    dt = fecha_hora
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt <= ref:
        raise FechaEnPasado("La fecha y hora deben ser futuras.")
