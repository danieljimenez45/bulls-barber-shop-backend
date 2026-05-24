from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import ContactMessageNotFound, IContactRepository
from app.infrastructure.persistence.orm.contact import ContactMessageORM


class SQLAlchemyContactRepository(IContactRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    # ── Traducción ORM → Entidad ──────────────────────────────────────────────

    @staticmethod
    def _to_entity(orm: ContactMessageORM) -> ContactMessage:
        return ContactMessage(
            id=orm.id,
            nombre=orm.nombre,
            email=orm.email,
            telefono=orm.telefono,
            asunto=orm.asunto,
            mensaje=orm.mensaje,
            leido=orm.leido,
            created_at=orm.created_at,
        )

    # ── Puerto ────────────────────────────────────────────────────────────────

    def save(self, message: ContactMessage) -> ContactMessage:
        orm = ContactMessageORM(
            nombre=message.nombre,
            email=message.email,
            telefono=message.telefono,
            asunto=message.asunto,
            mensaje=message.mensaje,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def list(
        self,
        solo_no_leidos: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ContactMessage], int]:
        query = self._session.query(ContactMessageORM)
        if solo_no_leidos:
            query = query.filter(ContactMessageORM.leido.is_(False))

        total = self._session.query(func.count(ContactMessageORM.id))
        if solo_no_leidos:
            total = total.filter(ContactMessageORM.leido.is_(False))
        total = total.scalar() or 0

        items = (
            query.order_by(ContactMessageORM.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_entity(o) for o in items], total

    def get_by_id(self, message_id: int) -> Optional[ContactMessage]:
        orm = (
            self._session.query(ContactMessageORM)
            .filter(ContactMessageORM.id == message_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def mark_as_read(self, message_id: int) -> ContactMessage:
        orm = (
            self._session.query(ContactMessageORM)
            .filter(ContactMessageORM.id == message_id)
            .first()
        )
        if not orm:
            raise ContactMessageNotFound(f"Mensaje {message_id} no encontrado")
        orm.leido = True
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)
