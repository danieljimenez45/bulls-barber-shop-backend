from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


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


class BookingOut(BookingCreate):
    id: int
    estado: str
    created_at: datetime

    model_config = {"from_attributes": True}
