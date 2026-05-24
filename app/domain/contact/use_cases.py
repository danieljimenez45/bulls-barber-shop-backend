"""
Casos de uso del dominio de mensajes de contacto.

B-24: se añaden casos de uso para persistencia, listado y marcado como leído.
"""

import logging
from typing import List, Optional, Tuple

from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import IContactNotifier, IContactRepository

logger = logging.getLogger(__name__)


class SendContactMessageUseCase:
    """
    Recibe un mensaje de contacto, lo persiste en BD (si hay repo disponible)
    y lo notifica al barbero (email u otro canal).
    """

    def __init__(
        self,
        notifier:   IContactNotifier,
        repository: Optional[IContactRepository] = None,
    ) -> None:
        self._notifier   = notifier
        self._repository = repository

    def execute(self, message: ContactMessage) -> ContactMessage:
        # 1. Persistir primero para obtener id y created_at
        if self._repository:
            message = self._repository.save(message)

        # 2. Notificar (el fallo en el notificador no deshace la persistencia)
        try:
            self._notifier.notify(message)
        except Exception:
            logger.exception("Error al notificar el mensaje de contacto id=%s", message.id)

        return message


class ListContactMessagesUseCase:
    """Lista los mensajes de contacto persistidos, paginados."""

    def __init__(self, repository: IContactRepository) -> None:
        self._repository = repository

    def execute(
        self,
        solo_no_leidos: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ContactMessage], int]:
        return self._repository.list(
            solo_no_leidos=solo_no_leidos,
            skip=skip,
            limit=limit,
        )


class MarkMessageReadUseCase:
    """Marca un mensaje como leído."""

    def __init__(self, repository: IContactRepository) -> None:
        self._repository = repository

    def execute(self, message_id: int) -> ContactMessage:
        return self._repository.mark_as_read(message_id)
