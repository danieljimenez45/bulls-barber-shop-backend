from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class GalleryImage:
    imagen_url: str
    id: Optional[int] = None
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: str = "corte"
    visible: bool = True
    orden: int = 0
    created_at: Optional[datetime] = None
