from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class GalleryImageOut(BaseModel):
    id: int
    imagen_url: str
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: str
    visible: bool
    orden: int
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
