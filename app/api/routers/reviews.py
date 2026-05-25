from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin, get_optional_admin
from app.api.dependencies.pagination import PaginationParams
from app.core.rate_limit import limiter
from app.api.schemas.pagination import PagedResponse
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


@router.get("/", response_model=PagedResponse[ReviewOut])
def listar_resenas(
    solo_visibles: bool = True,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    admin: AdminUser | None = Depends(get_optional_admin),
):
    """Lista reseñas paginadas.

    - Público (sin token): solo devuelve reseñas visibles (solo_visibles=true forzado).
    - Admin (con JWT válido): puede solicitar solo_visibles=false para ver las ocultas.

    Cualquier intento de pasar solo_visibles=false sin JWT válido devuelve 401.
    """
    if not solo_visibles and admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación para listar reseñas no visibles.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = SQLAlchemyReviewRepository(db)
    uc = ListReviewsUseCase(repo)
    items, total = uc.execute(solo_visibles=solo_visibles, skip=pagination.skip, limit=pagination.limit)
    return PagedResponse(
        items=[ReviewOut.model_validate(r) for r in items],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pagination.total_pages(total),
    )


@router.post("/", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def crear_resena(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    _rl: None = Depends(limiter(max_requests=5, window_seconds=60)),
):
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
