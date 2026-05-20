from typing import Optional

from sqlalchemy.orm import Session

from app.domain.auth.entity import AdminUser
from app.domain.auth.ports import IUserRepository
from app.infrastructure.persistence.orm.user import UserORM


class SQLAlchemyUserRepository(IUserRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_entity(orm: UserORM) -> AdminUser:
        return AdminUser(
            id=orm.id,
            email=orm.email,
            hashed_password=orm.hashed_password,
            is_active=orm.is_active,
            created_at=orm.created_at,
        )

    def find_by_email(self, email: str) -> Optional[AdminUser]:
        orm = (
            self._session.query(UserORM)
            .filter(UserORM.email == email)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def find_by_id(self, user_id: int) -> Optional[AdminUser]:
        orm = (
            self._session.query(UserORM)
            .filter(UserORM.id == user_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def create(self, user: AdminUser) -> AdminUser:
        orm = UserORM(
            email=user.email,
            hashed_password=user.hashed_password,
            is_active=user.is_active,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)
