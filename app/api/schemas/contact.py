from typing import Optional

from pydantic import BaseModel


class ContactMessageIn(BaseModel):
    nombre: str
    email: str
    telefono: Optional[str] = None
    asunto: Optional[str] = None
    mensaje: str
