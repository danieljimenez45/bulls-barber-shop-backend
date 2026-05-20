from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ReviewCreate(BaseModel):
    nombre: str
    valoracion: int
    comentario: Optional[str] = None

    @field_validator("valoracion")
    @classmethod
    def validar_valoracion(cls, v: int) -> int:
        if not 1 <= v <= 5:
            raise ValueError("La valoración debe estar entre 1 y 5")
        return v


class ReviewOut(BaseModel):
    id: int
    nombre: str
    valoracion: int
    comentario: Optional[str] = None
    visible: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
