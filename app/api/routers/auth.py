from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.schemas.auth import TokenResponse
from app.core.rate_limit import limiter
from app.database import get_db
from app.domain.auth.ports import InvalidCredentials
from app.domain.auth.use_cases import LoginUseCase
from app.infrastructure.persistence.repositories.user import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_hasher import BcryptPasswordHasher

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    # Máximo 5 intentos por IP en 60 segundos para frenar ataques de fuerza bruta.
    _rl: None = Depends(limiter(max_requests=5, window_seconds=60)),
):
    """
    Autentica al admin y devuelve un JWT.
    Recibe las credenciales como application/x-www-form-urlencoded (estándar OAuth2).
    El campo 'username' contiene el email del administrador.
    """
    try:
        user_repo = SQLAlchemyUserRepository(db)
        hasher = BcryptPasswordHasher()
        jwt_service = JWTService()
        uc = LoginUseCase(user_repo, hasher, jwt_service)
        token = uc.execute(form.username, form.password)
        return TokenResponse(access_token=token)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
