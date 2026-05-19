from typing import Optional
from pydantic import BaseModel


class ServiceBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    duracion_minutos: int = 30
    categoria: str = "corte"
    imagen_url: Optional[str] = None
    activo: bool = True
    orden: int = 0


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio: Optional[float] = None
    duracion_minutos: Optional[int] = None
    categoria: Optional[str] = None
    imagen_url: Optional[str] = None
    activo: Optional[bool] = None
    orden: Optional[int] = None


class ServiceOut(ServiceBase):
    id: int

    model_config = {"from_attributes": True}
