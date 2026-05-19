from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.booking import Booking
from app.schemas.booking import BookingCreate, BookingOut, BookingUpdate

router = APIRouter()

ESTADOS_VALIDOS = {"pendiente", "confirmada", "cancelada", "completada"}


@router.get("/", response_model=List[BookingOut])
def listar_reservas(
    estado: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Booking)
    if estado:
        query = query.filter(Booking.estado == estado)
    return query.order_by(Booking.fecha_hora).all()


@router.get("/{booking_id}", response_model=BookingOut)
def obtener_reserva(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return booking


@router.post("/", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
def crear_reserva(data: BookingCreate, db: Session = Depends(get_db)):
    booking = Booking(**data.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.patch("/{booking_id}", response_model=BookingOut)
def actualizar_reserva(
    booking_id: int, data: BookingUpdate, db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    updates = data.model_dump(exclude_unset=True)
    if "estado" in updates and updates["estado"] not in ESTADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Estado no válido. Usa uno de: {ESTADOS_VALIDOS}",
        )
    for field, value in updates.items():
        setattr(booking, field, value)
    db.commit()
    db.refresh(booking)
    return booking


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_reserva(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    booking.estado = "cancelada"
    db.commit()
