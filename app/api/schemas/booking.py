"""Schemas Pydantic para el dominio de reservas."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class BookingCreate(BaseModel):
    nombre_cliente: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre completo del cliente.",
    )
    telefono: str = Field(
        ...,
        min_length=6,
        max_length=20,
        description="Teléfono de contacto (solo dígitos y guiones).",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Correo electrónico opcional para confirmaciones.",
    )
    servicio_id: int = Field(..., gt=0, description="ID del servicio seleccionado.")
    servicio_nombre: Optional[str] = Field(None, max_length=100)
    fecha_hora: datetime = Field(..., description="Fecha y hora del turno (ISO 8601).")
    barbero: Optional[str] = Field("Cualquier barbero", max_length=100)
    notas: Optional[str] = Field(None, max_length=500)


class BookingUpdate(BaseModel):
    # Solo se aceptan transiciones de estado conocidas para evitar valores arbitrarios en BD.
    estado: Optional[Literal["pendiente", "confirmada", "cancelada", "completada"]] = None
    notas: Optional[str] = Field(None, max_length=500)
    barbero: Optional[str] = Field(None, max_length=100)


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
    deleted_at: Optional[datetime] = None  # None = activa, timestamp = soft-deleted

    model_config = {"from_attributes": True}


class DisponibilidadOut(BaseModel):
    fecha: date
    slots_ocupados: List[datetime]
