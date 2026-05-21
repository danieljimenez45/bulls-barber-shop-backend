from typing import Optional

from pydantic import BaseModel, EmailStr


class ContactMessageIn(BaseModel):
    nombre: str
    email: EmailStr
    telefono: Optional[str] = None
    asunto: Optional[str] = None
    mensaje: str
