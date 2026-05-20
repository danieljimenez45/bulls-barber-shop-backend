from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.schemas.gallery import GalleryImageOut
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
from app.infrastructure.storage.local import LocalFileStorage

router = APIRouter()


# ── Públicos ───────────────────────────────────────────────────────────────────


@router.get("/", response_model=List[GalleryImageOut])
def listar_imagenes(
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista imágenes visibles de la galería."""
    repo = SQLAlchemyGalleryRepository(db)
    uc = ListImagesUseCase(repo)
    images = uc.execute(categoria=categoria)
    return [GalleryImageOut.model_validate(img) for img in images]


# ── Protegidos (solo admin) ────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=GalleryImageOut,
    status_code=status.HTTP_201_CREATED,
)
async def subir_imagen(
    file: UploadFile = File(...),
    titulo: Optional[str] = None,
    categoria: str = "corte",
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """Sube una imagen a la galería. Solo accesible para el admin."""
    import os

    ext = os.path.splitext(file.filename or "")[1].lower()
    file_data = await file.read()
    repo = SQLAlchemyGalleryRepository(db)
    storage = LocalFileStorage()
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
    storage = LocalFileStorage()
    uc = DeleteImageUseCase(repo, storage)
    try:
        uc.execute(image_id)
    except ImageNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
