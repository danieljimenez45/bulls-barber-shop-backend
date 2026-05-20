from app.domain.auth.entity import AdminUser
from app.domain.auth.ports import (
    InvalidCredentials,
    IPasswordHasher,
    ITokenService,
    IUserRepository,
)


class LoginUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repo
        self._password_hasher = password_hasher
        self._token_service = token_service

    def execute(self, email: str, password: str) -> str:
        """Autentica al admin y devuelve un JWT. Lanza InvalidCredentials si falla."""
        user = self._user_repo.find_by_email(email)
        if not user or not user.is_active:
            raise InvalidCredentials("Credenciales inválidas")
        if not self._password_hasher.verify(password, user.hashed_password):
            raise InvalidCredentials("Credenciales inválidas")
        return self._token_service.create_token({"sub": str(user.id)})


class GetCurrentAdminUseCase:
    """Verifica un JWT y devuelve el AdminUser correspondiente."""

    def __init__(
        self,
        user_repo: IUserRepository,
        token_service: ITokenService,
    ) -> None:
        self._user_repo = user_repo
        self._token_service = token_service

    def execute(self, token: str) -> AdminUser:
        from app.domain.auth.ports import TokenInvalid  # evitar circular import

        payload = self._token_service.decode_token(token)  # lanza TokenInvalid si falla
        user_id = payload.get("sub")
        if not user_id:
            raise TokenInvalid("Token sin subject")
        user = self._user_repo.find_by_id(int(user_id))
        if not user or not user.is_active:
            raise TokenInvalid("Usuario no encontrado o inactivo")
        return user
