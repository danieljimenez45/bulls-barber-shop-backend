from abc import ABC, abstractmethod
from typing import Optional

from app.domain.auth.entity import AdminUser


class InvalidCredentials(Exception):
    """Credenciales inválidas (email no existe o contraseña incorrecta).
    Usamos un mensaje genérico para no revelar cuál de los dos falló.
    """


class TokenInvalid(Exception):
    """El JWT es inválido, está expirado o su firma no coincide."""


class IUserRepository(ABC):

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[AdminUser]: ...

    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[AdminUser]: ...

    @abstractmethod
    def create(self, user: AdminUser) -> AdminUser: ...


class IPasswordHasher(ABC):

    @abstractmethod
    def hash(self, plain_password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class ITokenService(ABC):

    @abstractmethod
    def create_token(self, payload: dict) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict:
        """Devuelve el payload decodificado o lanza TokenInvalid."""
