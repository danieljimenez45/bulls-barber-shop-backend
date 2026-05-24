from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.dependencies.pagination import PaginationParams
from app.api.schemas.gallery import GalleryImageOut
from app.api.schemas.pagination import PagedResponse
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.gallery.ports import ImageNotFound
from app.domain.gallery.use_cases import (
    DeleteImageUseCase,
    ListImagesUseCase,
    UploadImageUseCase,
)
from app.infrastructure.persistence.repositories.gallery import (
    SQLAlchemyGalleryRepository,
)
from app.infrastructure.storage import get_file_storage

router = APIRouter()


# ── Públicos ───────────────────────────────────────────────────────────────────


@router.get("/", response_model=PagedResponse[GalleryImageOut])
def listar_imagenes(
    categoria: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
):
    """Lista imágenes visibles de la galería, paginadas."""
    repo = SQLAlchemyGalleryRepository(db)
    uc = ListImagesUseCase(repo)
    items, total = uc.execute(categoria=categoria, skip=pagination.skip, limit=pagination.limit)
    return PagedResponse(
        items=[GalleryImageOut.model_validate(img) for img in items],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pagination.total_pages(total),
    )


# ── Protegidos (solo admin) ────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=GalleryImageOut,
    status_code=status.HTTP_201_CREATED,
)
async def subir_imagen(
    file: UploadFile = File(...),
    titulo: Optional[str] = Form(None),
    categoria: str = Form("corte"),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """Sube una imagen a la galería. Solo accesible para el admin."""
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    file_data = await file.read()
    repo = SQLAlchemyGalleryRepository(db)
    storage = get_file_storage()
    uc = UploadImageUseCase(repo, storage)
    try:
        image = uc.execute(file_data, ext, titulo=titulo, categoria=categoria)
        return GalleryImageOut.model_validate(image)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_imagen(
    image_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyGalleryRepository(db)
    storage = get_file_storage()
    uc = DeleteImageUseCase(repo, storage)
    try:
        uc.execute(image_id)
    except ImageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
