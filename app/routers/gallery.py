from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
import os, uuid, shutil

from app.database import get_db
from app.models.gallery import GalleryImage
from app.schemas.gallery import GalleryImageCreate, GalleryImageOut

router = APIRouter()
UPLOAD_DIR = "uploads/gallery"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/", response_model=List[GalleryImageOut])
def listar_imagenes(
    categoria: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(GalleryImage).filter(GalleryImage.visible == True)  # noqa
    if categoria:
        query = query.filter(GalleryImage.categoria == categoria)
    return query.order_by(GalleryImage.orden, GalleryImage.created_at.desc()).all()


@router.post("/upload", response_model=GalleryImageOut, status_code=status.HTTP_201_CREATED)
async def subir_imagen(
    file: UploadFile = File(...),
    titulo: Optional[str] = None,
    categoria: str = "corte",
    db: Session = Depends(get_db),
):
    """Sube una imagen a la galería."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=400, detail="Formato no permitido. Usa JPG, PNG o WebP.")
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    image = GalleryImage(
        titulo=titulo,
        imagen_url=f"/uploads/gallery/{filename}",
        categoria=categoria,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_imagen(image_id: int, db: Session = Depends(get_db)):
    image = db.query(GalleryImage).filter(GalleryImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Imagen no encontrada")
    # Eliminar archivo físico
    local_path = image.imagen_url.lstrip("/")
    if os.path.exists(local_path):
        os.remove(local_path)
    db.delete(image)
    db.commit()
