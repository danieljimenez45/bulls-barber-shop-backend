from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GalleryImageCreate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: str
    categoria: str = "corte"
    visible: bool = True
    orden: int = 0


class GalleryImageOut(GalleryImageCreate):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
