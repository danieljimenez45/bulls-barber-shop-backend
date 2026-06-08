"""Schemas Pydantic para el dominio de reservas."""

import re
from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.constants import DEFAULT_BARBER
from app.domain.booking.rules import (
    FechaEnPasado,
    SlotFueraDeGrid,
    assert_future_datetime,
    assert_slot_en_grid,
)

# Teléfonos españoles: móviles (6/7) y fijos (8/9), 9 dígitos en total.
# Admite opcionalmente el prefijo internacional +34 o 0034.
_TELEFONO_RE = re.compile(r"^(?:\+34|0034)?[6789]\d{8}$")


class BookingCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,  # elimina espacios al inicio/fin de strings
        extra="forbid",             # rechaza cualquier campo no declarado → 422
    )

    nombre_cliente: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nombre completo del cliente.",
    )
    telefono: str = Field(
        ...,
        description="Teléfono español de 9 dígitos (móvil 6/7 o fijo 8/9). "
                    "Admite prefijo +34 o 0034.",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Correo electrónico opcional para confirmaciones.",
    )
    servicio_id: int = Field(..., gt=0, description="ID del servicio seleccionado.")
    # servicio_nombre se omite intencionadamente: el backend lo obtiene de BD
    # a partir de servicio_id y lo ignora si el cliente lo enviara.
    fecha_hora: datetime = Field(..., description="Fecha y hora del turno (ISO 8601).")
    barbero: Optional[str] = Field(DEFAULT_BARBER, max_length=100)
    notas: Optional[str] = Field(None, max_length=500)

    @field_validator("telefono")
    @classmethod
    def telefono_valido(cls, v: str) -> str:
        # str_strip_whitespace ya eliminó espacios extremos; comprobamos formato.
        if not _TELEFONO_RE.match(v):
            raise ValueError(
                "El teléfono debe tener 9 dígitos y empezar por 6, 7, 8 o 9 "
                "(admite prefijo +34 o 0034)."
            )
        return v

    @field_validator("fecha_hora")
    @classmethod
    def fecha_debe_ser_futura_y_en_grid(cls, v: datetime) -> datetime:
        try:
            assert_future_datetime(v)
        except FechaEnPasado as exc:
            raise ValueError(str(exc)) from exc
        try:
            assert_slot_en_grid(v)
        except SlotFueraDeGrid as exc:
            raise ValueError(str(exc)) from exc
        return v


class BookingUpdate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    # Solo se aceptan transiciones de estado vía PATCH.
    # "cancelada" se excluye deliberadamente: la cancelación debe hacerse
    # siempre a través de DELETE /api/bookings/{id}, que ejecuta el soft-delete
    # consistente (deleted_at + estado=cancelada). Un PATCH con cancelada
    # dejaría la fila sin deleted_at y rompería las reglas de slot ocupado.
    estado: Optional[Literal["pendiente", "confirmada", "completada"]] = None
    notas: Optional[str] = Field(None, max_length=500)
    barbero: Optional[str] = Field(None, max_length=100)


class BookingOut(BaseModel):
    id: int
    nombre_cliente: str
    telefono: str
    email: Optional[str] = None
    servicio_id: int
    servicio_nombre: Optional[str] = None
    duracion_minutos: int = 30
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
