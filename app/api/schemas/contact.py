from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ContactMessageIn(BaseModel):
    nombre:   str
    email:    EmailStr
    telefono: Optional[str] = None
    asunto:   Optional[str] = None
    mensaje:  str


class ContactMessageOut(BaseModel):
    """Respuesta del admin al listar mensajes (B-24)."""

    id:         int
    nombre:     str
    email:      str
    telefono:   Optional[str]      = None
    asunto:     Optional[str]      = None
    mensaje:    str
    leido:      bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
