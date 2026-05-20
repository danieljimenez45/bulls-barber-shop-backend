from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.domain.auth.ports import ITokenService, TokenInvalid


class JWTService(ITokenService):
    """Implementación de ITokenService usando PyJWT con HS256."""

    def create_token(self, payload: dict) -> str:
        data = payload.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        data["exp"] = expire
        return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenInvalid("Token expirado") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenInvalid("Token inválido") from exc
