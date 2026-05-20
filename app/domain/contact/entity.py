from dataclasses import dataclass
from typing import Optional


@dataclass
class ContactMessage:
    nombre: str
    email: str
    mensaje: str
    telefono: Optional[str] = None
    asunto: Optional[str] = None
