from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import List, Optional

from app.domain.booking.entity import Booking


class BookingNotFound(Exception):
    """Se lanza cuando no se encuentra una reserva por su ID."""


class SlotOcupado(Exception):
    """El slot fecha+hora ya tiene una cita activa (no cancelada)."""


class IBookingNotifier(ABC):
    """Puerto de notificación: se llama tras crear una reserva."""

    @abstractmethod
    def notify_new_booking(self, booking: "Booking") -> None:
        """Notifica al cliente y/o al admin sobre la nueva reserva."""


class IBookingRepository(ABC):

    @abstractmethod
    def create(self, booking: Booking) -> Booking: ...

    @abstractmethod
    def get_by_id(self, booking_id: int) -> Optional[Booking]: ...

    @abstractmethod
    def list(self, estado: Optional[str] = None) -> List[Booking]: ...

    @abstractmethod
    def update(self, booking: Booking) -> Booking: ...

    @abstractmethod
    def delete(self, booking_id: int) -> None:
        """Soft-delete: marca la reserva como cancelada."""

    @abstractmethod
    def is_slot_available(self, fecha_hora: datetime) -> bool:
        """True si no existe ninguna cita activa (no cancelada) en esa fecha+hora exacta."""

    @abstractmethod
    def get_slots_ocupados(self, fecha: date) -> List[datetime]:
        """Devuelve las horas ocupadas (no canceladas) en la fecha dada."""
