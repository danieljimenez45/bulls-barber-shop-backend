from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.schemas.booking import (
    BookingCreate,
    BookingOut,
    BookingUpdate,
    DisponibilidadOut,
)
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, SlotOcupado
from app.domain.booking.use_cases import (
    CancelBookingUseCase,
    CreateBookingUseCase,
    GetBookingUseCase,
    GetDisponibilidadUseCase,
    ListBookingsUseCase,
    UpdateBookingUseCase,
)
from app.infrastructure.notifications.booking_notifier import SMTPBookingNotifier
from app.infrastructure.persistence.repositories.booking import (
    SQLAlchemyBookingRepository,
)

router = APIRouter()


# ── Públicos ───────────────────────────────────────────────────────────────────


@router.get("/disponibilidad", response_model=DisponibilidadOut)
def get_disponibilidad(
    fecha: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Devuelve los slots ya ocupados en una fecha dada.
    El frontend usa esta respuesta para deshabilitar horas no disponibles.
    Acceso público — no requiere autenticación.
    """
    repo = SQLAlchemyBookingRepository(db)
    uc = GetDisponibilidadUseCase(repo)
    slots = uc.execute(fecha)
    return DisponibilidadOut(fecha=fecha, slots_ocupados=slots)


@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def crear_reserva(data: BookingCreate, db: Session = Depends(get_db)):
    """
    Crea una reserva (acceso público — el cliente la solicita desde la web).
    Devuelve 409 si ya existe una cita activa en esa fecha+hora.
    """
    booking = Booking(
        nombre_cliente=data.nombre_cliente,
        telefono=data.telefono,
        email=data.email,
        servicio_id=data.servicio_id,
        servicio_nombre=data.servicio_nombre,
        fecha_hora=data.fecha_hora,
        barbero=data.barbero or "Cualquier barbero",
        notas=data.notas,
    )
    repo = SQLAlchemyBookingRepository(db)
    notifier = SMTPBookingNotifier()
    uc = CreateBookingUseCase(repo, notifier)
    try:
        created = uc.execute(booking)
        return BookingOut.model_validate(created)
    except SlotOcupado as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ── Protegidos (solo admin) ────────────────────────────────────────────────────


@router.get("/", response_model=List[BookingOut])
def listar_reservas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """Lista todas las reservas. Solo accesible para el admin."""
    repo = SQLAlchemyBookingRepository(db)
    uc = ListBookingsUseCase(repo)
    bookings = uc.execute(estado=estado)
    return [BookingOut.model_validate(b) for b in bookings]


@router.get("/{booking_id}", response_model=BookingOut)
def obtener_reserva(
    booking_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyBookingRepository(db)
    uc = GetBookingUseCase(repo)
    try:
        booking = uc.execute(booking_id)
        return BookingOut.model_validate(booking)
    except BookingNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{booking_id}", response_model=BookingOut)
def actualizar_reserva(
    booking_id: int,
    data: BookingUpdate,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyBookingRepository(db)
    uc = UpdateBookingUseCase(repo)
    try:
        updated = uc.execute(booking_id, **data.model_dump(exclude_unset=True))
        return BookingOut.model_validate(updated)
    except BookingNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_reserva(
    booking_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyBookingRepository(db)
    uc = CancelBookingUseCase(repo)
    try:
        uc.execute(booking_id)
    except BookingNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
