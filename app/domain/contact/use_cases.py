"""
Casos de uso del dominio de mensajes de contacto.

B-24: persistencia, listado y marcado como leído.
"""

from typing import List, Tuple

from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import IContactNotifier, IContactRepository


class SendContactMessageUseCase:
    """
    Recibe un mensaje de contacto, lo persiste en BD y lo notifica al barbero.
    """

    def __init__(
        self,
        notifier: IContactNotifier,
        repository: IContactRepository,
    ) -> None:
        self._notifier = notifier
        self._repository = repository

    def execute(self, message: ContactMessage) -> ContactMessage:
        message = self._repository.save(message)
        self._notifier.notify(message)
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
