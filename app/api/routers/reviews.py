from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.schemas.review import ReviewCreate, ReviewOut
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.review.entity import Review
from app.domain.review.ports import ReviewNotFound
from app.domain.review.use_cases import (
    CreateReviewUseCase,
    DeleteReviewUseCase,
    ListReviewsUseCase,
    ToggleVisibilityUseCase,
)
from app.infrastructure.persistence.repositories.review import (
    SQLAlchemyReviewRepository,
)

router = APIRouter()


# ── Públicos ───────────────────────────────────────────────────────────────────


@router.get("/", response_model=List[ReviewOut])
def listar_resenas(
    solo_visibles: bool = True,
    db: Session = Depends(get_db),
):
    """Lista reseñas visibles (público) o todas (admin pasa solo_visibles=false)."""
    repo = SQLAlchemyReviewRepository(db)
    uc = ListReviewsUseCase(repo)
    reviews = uc.execute(solo_visibles=solo_visibles)
    return [ReviewOut.model_validate(r) for r in reviews]


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def crear_resena(data: ReviewCreate, db: Session = Depends(get_db)):
    """Crea una reseña (acceso público — cualquier cliente puede dejar una)."""
    review = Review(
        nombre=data.nombre,
        valoracion=data.valoracion,
        comentario=data.comentario,
    )
    repo = SQLAlchemyReviewRepository(db)
    uc = CreateReviewUseCase(repo)
    created = uc.execute(review)
    return ReviewOut.model_validate(created)


# ── Protegidos (solo admin) ────────────────────────────────────────────────────


@router.patch("/{review_id}/visibilidad", response_model=ReviewOut)
def cambiar_visibilidad(
    review_id: int,
    visible: bool,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """Muestra u oculta una reseña. Solo accesible para el admin."""
    repo = SQLAlchemyReviewRepository(db)
    uc = ToggleVisibilityUseCase(repo)
    try:
        updated = uc.execute(review_id, visible)
        return ReviewOut.model_validate(updated)
    except ReviewNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_resena(
    review_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyReviewRepository(db)
    uc = DeleteReviewUseCase(repo)
    try:
        uc.execute(review_id)
    except ReviewNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
