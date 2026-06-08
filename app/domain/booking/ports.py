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
    def list(
        self,
        estado: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Booking]: ...

    @abstractmethod
    def count(self, estado: Optional[str] = None) -> int: ...

    @abstractmethod
    def update(self, booking: Booking) -> Booking: ...

    @abstractmethod
    def delete(self, booking_id: int) -> None:
        """Soft-delete: marca la reserva como cancelada."""

    @abstractmethod
    def is_slot_available(self, fecha_hora: datetime, duracion_minutos: int = 30) -> bool:
        """True si el intervalo [fecha_hora, fecha_hora+duracion_minutos) no solapa
        con ninguna cita activa existente."""

    @abstractmethod
    def get_slots_ocupados(self, fecha: date) -> List[datetime]:
        """Devuelve las horas ocupadas (no canceladas) en la fecha dada."""

    @abstractmethod
    def list_by_date_range(self, desde: date, hasta: date) -> List[Booking]:
        """Devuelve todas las reservas cuya fecha_hora cae en [desde, hasta] (ambos inclusive),
        ordenadas por fecha_hora ascendente."""
