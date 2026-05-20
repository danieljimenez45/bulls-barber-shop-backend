import logging

from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import IContactNotifier

logger = logging.getLogger(__name__)


class LogContactNotifier(IContactNotifier):
    """Adaptador inline (simple): loguea el mensaje hasta que haya email real."""

    def notify(self, message: ContactMessage) -> None:
        logger.info(
            "[CONTACTO] De: %s (%s) — Asunto: %s — %s",
            message.nombre,
            message.email,
            message.asunto or "(sin asunto)",
            message.mensaje,
        )


class SendContactMessageUseCase:
    def __init__(self, notifier: IContactNotifier) -> None:
        self._notifier = notifier

    def execute(self, message: ContactMessage) -> None:
        self._notifier.notify(message)
