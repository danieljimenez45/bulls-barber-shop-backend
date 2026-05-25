"""
Router de galería.

El endpoint de subida valida el archivo antes de procesarlo:
  - Tamaño máximo de 5 MB.
  - Solo se aceptan extensiones de imagen: .jpg, .jpeg, .png, .webp.
  - Se rechaza cualquier nombre con doble extensión (p.ej. foto.jpg.exe).
  - Se verifica con Pillow que los bytes son realmente una imagen válida,
    impidiendo que se suban archivos disfrazados con extensión de imagen.
"""

import io
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
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

# ── Constantes de validación ───────────────────────────────────────────────────

_MAX_SIZE_BYTES = 5 * 1024 * 1024          # 5 MB
_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _validate_upload(file_data: bytes, filename: str) -> str:
    """
    Valida el archivo subido y devuelve la extensión normalizada.

    Lanza HTTPException 400 si:
      - El tamaño supera 5 MB.
      - La extensión no está en la lista blanca.
      - El nombre tiene doble extensión (p.ej. foto.jpg.exe).
      - Los bytes no corresponden a una imagen real (verificación Pillow).
    """
    # 1. Tamaño
    if len(file_data) > _MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo supera el límite de 5 MB.",
        )

    # 2. Extensión y doble extensión
    name_without_ext, ext = os.path.splitext(filename.lower())
    if ext not in _ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(_ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida. Formatos aceptados: {allowed}.",
        )
    # Doble extensión: si el nombre sin la última extensión sigue teniendo extensión,
    # el archivo tiene un nombre compuesto peligroso (p.ej. foto.jpg.exe).
    if os.path.splitext(name_without_ext)[1]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de archivo con doble extensión no permitido.",
        )

    # 3. Validación de contenido con Pillow
    try:
        img = Image.open(io.BytesIO(file_data))
        img.verify()  # verify() detecta imágenes corruptas o falsificadas
    except (UnidentifiedImageError, Exception):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es una imagen válida.",
        )

    return ext


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
    """
    Sube una imagen a la galería. Solo accesible para el admin.

    Validaciones aplicadas:
    - Máximo 5 MB.
    - Extensiones permitidas: .jpg, .jpeg, .png, .webp.
    - Sin doble extensión.
    - El contenido debe ser una imagen real (verificado con Pillow).
    """
    file_data = await file.read()
    ext = _validate_upload(file_data, file.filename or "")

    repo = SQLAlchemyGalleryRepository(db)
    storage = get_file_storage()
    uc = UploadImageUseCase(repo, storage)
    try:
        image = uc.execute(file_data, ext, titulo=titulo, categoria=categoria)
        return GalleryImageOut.model_validate(image)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
