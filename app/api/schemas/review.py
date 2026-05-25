"""Schemas Pydantic para el dominio de reseñas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
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


class ReviewOut(BaseModel):
    id: int
    nombre: str
    valoracion: int
    comentario: Optional[str] = None
    visible: bool
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
