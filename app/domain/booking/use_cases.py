from datetime import date, datetime
from typing import List, Optional, Tuple

from app.domain.booking.entity import Booking
from app.domain.booking.ports import (
    BookingNotFound,
    IBookingNotifier,
    IBookingRepository,
    SlotOcupado,
)


class CreateBookingUseCase:
    def __init__(
        self,
        repo: IBookingRepository,
        notifier: Optional[IBookingNotifier] = None,
    ) -> None:
        self._repo = repo
        self._notifier = notifier

    def execute(self, booking: Booking) -> Booking:
        """Crea la reserva si el slot está libre; lanza SlotOcupado si no.
        Tras crear, dispara la notificación si hay notifier configurado."""
        if not self._repo.is_slot_available(booking.fecha_hora):
            raise SlotOcupado(
                f"El horario {booking.fecha_hora.strftime('%d/%m/%Y a las %H:%M')} "
                "ya está reservado. Por favor elige otro horario."
            )
        created = self._repo.create(booking)
        if self._notifier:
            self._notifier.notify_new_booking(created)
        return created


class GetBookingUseCase:
    def __init__(self, repo: IBookingRepository) -> None:
        self._repo = repo

    def execute(self, booking_id: int) -> Booking:
        booking = self._repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFound(f"Reserva {booking_id} no encontrada")
        return booking


class ListBookingsUseCase:
    def __init__(self, repo: IBookingRepository) -> None:
        self._repo = repo

    def execute(
        self,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Tuple[List[Booking], int]:
        items = self._repo.list(estado=estado, skip=skip, limit=limit)
        total = self._repo.count(estado=estado)
        return items, total


class UpdateBookingUseCase:
    def __init__(self, repo: IBookingRepository) -> None:
        self._repo = repo

    def execute(
        self,
        booking_id: int,
        estado: Optional[str] = None,
        notas: Optional[str] = None,
        barbero: Optional[str] = None,
    ) -> Booking:
        booking = self._repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFound(f"Reserva {booking_id} no encontrada")
        if estado is not None:
            booking.cambiar_estado(estado)  # valida en la entidad
        if notas is not None:
            booking.notas = notas
        if barbero is not None:
            booking.barbero = barbero
        return self._repo.update(booking)


class CancelBookingUseCase:
    def __init__(self, repo: IBookingRepository) -> None:
        self._repo = repo

    def execute(self, booking_id: int) -> None:
        booking = self._repo.get_by_id(booking_id)
        if not booking:
            raise BookingNotFound(f"Reserva {booking_id} no encontrada")
        self._repo.delete(booking_id)


class GetDisponibilidadUseCase:
    """Devuelve los slots ocupados en una fecha para que el frontend los deshabilite."""

    def __init__(self, repo: IBookingRepository) -> None:
        self._repo = repo

    def execute(self, fecha: date) -> List[datetime]:
        return self._repo.get_slots_ocupados(fecha)
