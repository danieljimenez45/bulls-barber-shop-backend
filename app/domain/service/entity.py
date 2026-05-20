from dataclasses import dataclass
from typing import Optional


@dataclass
class Service:
    nombre: str
    precio: float
    id: Optional[int] = None
    descripcion: Optional[str] = None
    duracion_minutos: int = 30
    categoria: str = "corte"
    imagen_url: Optional[str] = None
    activo: bool = True
    orden: int = 0
