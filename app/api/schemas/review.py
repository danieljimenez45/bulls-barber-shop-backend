"""Schemas Pydantic para el dominio de reseñas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,  # elimina espacios al inicio/fin de strings
        extra="forbid",             # rechaza cualquier campo no declarado → 422
    )

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre del autor de la reseña.",
    )
    valoracion: int = Field(
        ...,
        ge=1,
        le=5,
        description="Puntuación entre 1 (mínimo) y 5 (máximo).",
    )
    comentario: Optional[str] = Field(
        None,
        max_length=1000,
        description="Texto libre opcional de la reseña.",
    )

    @field_validator("comentario")
    @classmethod
    def comentario_no_vacio(cls, v: Optional[str]) -> Optional[str]:
        # str_strip_whitespace ya limpió espacios; si queda una cadena vacía
        # la tratamos igual que None para evitar comentarios de relleno.
        if v is not None and len(v) == 0:
            return None
        if v is not None and len(v) < 10:
            raise ValueError("El comentario debe tener al menos 10 caracteres.")
        return v


class ReviewOut(BaseModel):
    id: int
    nombre: str
    valoracion: int
    comentario: Optional[str] = None
    visible: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
