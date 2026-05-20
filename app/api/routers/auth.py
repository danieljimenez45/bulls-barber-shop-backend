from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import LoginRequest, TokenResponse
from app.database import get_db
from app.domain.auth.ports import InvalidCredentials
from app.domain.auth.use_cases import LoginUseCase
from app.infrastructure.persistence.repositories.user import SQLAlchemyUserRepository
from app.infrastructure.security.jwt_service import JWTService
from app.infrastructure.security.password_hasher import BcryptPasswordHasher

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Autentica al admin y devuelve un JWT."""
    try:
        user_repo = SQLAlchemyUserRepository(db)
        hasher = BcryptPasswordHasher()
        jwt_service = JWTService()
        uc = LoginUseCase(user_repo, hasher, jwt_service)
        token = uc.execute(data.email, data.password)
        return TokenResponse(access_token=token)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
