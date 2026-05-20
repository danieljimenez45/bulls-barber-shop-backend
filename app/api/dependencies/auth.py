from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.auth.ports import TokenInvalid
from app.domain.auth.use_cases import GetCurrentAdminUseCase
from app.infrastructure.persistence.repositories.user import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_service import JWTService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Dependencia FastAPI: extrae y valida el JWT; devuelve el AdminUser activo."""
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
