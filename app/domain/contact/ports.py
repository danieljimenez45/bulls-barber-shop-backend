from abc import ABC, abstractmethod

from app.domain.contact.entity import ContactMessage


class IContactNotifier(ABC):
    """Puerto para notificar al barbero cuando llega un mensaje de contacto."""

    @abstractmethod
    def notify(self, message: ContactMessage) -> None: ...
