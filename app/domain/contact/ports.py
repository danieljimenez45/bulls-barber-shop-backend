from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.contact.entity import ContactMessage


class IContactNotifier(ABC):
    """Puerto para notificar al barbero cuando llega un mensaje de contacto."""

    @abstractmethod
    def notify(self, message: ContactMessage) -> None: ...


class ContactMessageNotFound(Exception):
    """Se lanza cuando no se encuentra un mensaje por su ID."""


class IContactRepository(ABC):
    """Puerto de persistencia para mensajes de contacto (B-24)."""

    @abstractmethod
    def save(self, message: ContactMessage) -> ContactMessage:
        """Persiste el mensaje y devuelve la entidad con id y created_at asignados."""

    @abstractmethod
    def list(
        self,
        solo_no_leidos: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[ContactMessage], int]:
        """Devuelve (items, total) ordenados por created_at desc."""

    @abstractmethod
    def mark_as_read(self, message_id: int) -> ContactMessage:
        """Marca el mensaje como leído y lo devuelve actualizado."""

    @abstractmethod
    def get_by_id(self, message_id: int) -> Optional[ContactMessage]:
        """Devuelve el mensaje o None si no existe."""
