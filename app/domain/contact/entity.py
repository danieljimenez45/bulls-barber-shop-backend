from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ContactMessage:
    """
    Entidad de dominio que representa un mensaje del formulario de contacto.
    B-24: se añaden id, leido y created_at para soportar persistencia en BD.
    """

    nombre:     str
    email:      str
    mensaje:    str
    telefono:   Optional[str]      = None
    asunto:     Optional[str]      = None
    # Campos de persistencia (None cuando aún no se ha guardado)
    id:         Optional[int]      = None
    leido:      bool               = False
    created_at: Optional[datetime] = None
