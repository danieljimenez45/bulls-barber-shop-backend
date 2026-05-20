from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


class BookingCreate(BaseModel):
    nombre_cliente: str
    telefono: str
    email: Optional[str] = None
    servicio_id: int
    servicio_nombre: Optional[str] = None
    fecha_hora: datetime
    barbero: Optional[str] = "Cualquier barbero"
    notas: Optional[str] = None


class BookingUpdate(BaseModel):
    estado: Optional[str] = None
    notas: Optional[str] = None
    barbero: Optional[str] = None


class BookingOut(BaseModel):
    id: int
    nombre_cliente: str
    telefono: str
    email: Optional[str] = None
    servicio_id: int
    servicio_nombre: Optional[str] = None
    fecha_hora: datetime
    barbero: str
    notas: Optional[str] = None
    estado: str
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DisponibilidadOut(BaseModel):
    fecha: date
    slots_ocupados: List[datetime]
