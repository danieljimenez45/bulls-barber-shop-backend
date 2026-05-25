from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.auth.ports import TokenInvalid
from app.domain.auth.use_cases import GetCurrentAdminUseCase
from app.infrastructure.persistence.repositories.user import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_service import JWTService

# auto_error=True → lanza 401 automáticamente si no hay token (uso en endpoints protegidos)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# auto_error=False → devuelve None si no hay token (uso en endpoints opcionalmente protegidos)
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login", auto_error=False
)


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Dependencia FastAPI: extrae y valida el JWT; devuelve el AdminUser activo.
    Uso: endpoints que SIEMPRE requieren autenticación.
    """
    try:
        user_repo = SQLAlchemyUserRepository(db)
        jwt_service = JWTService()
        uc = GetCurrentAdminUseCase(user_repo, jwt_service)
        return uc.execute(token)
    except TokenInvalid as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_optional_admin(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> Optional[AdminUser]:
    """Dependencia FastAPI: devuelve el AdminUser si hay JWT válido, None si no hay token.
    Uso: endpoints que son públicos por defecto pero requieren admin para ciertas operaciones.
    Si hay token pero es inválido, lanza 401 igualmente.
    """
    if token is None:
        return None
    try:
        user_repo = SQLAlchemyUserRepository(db)
        jwt_service = JWTService()
        uc = GetCurrentAdminUseCase(user_repo, jwt_service)
        return uc.execute(token)
    except TokenInvalid as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
