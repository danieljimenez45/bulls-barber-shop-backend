import csv
import io
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.dependencies.pagination import PaginationParams
from app.core.constants import DEFAULT_BARBER
from app.core.rate_limit import limiter
from app.api.schemas.booking import (
    BookingCreate,
    BookingOut,
    BookingUpdate,
    DisponibilidadOut,
)
from app.api.schemas.pagination import PagedResponse
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.booking.entity import Booking
from app.domain.booking.ports import BookingNotFound, SlotOcupado
from app.domain.booking.use_cases import (
    CancelBookingUseCase,
    CreateBookingUseCase,
    ExportBookingsCSVUseCase,
    GetBookingUseCase,
    GetDisponibilidadUseCase,
    ListBookingsUseCase,
    UpdateBookingUseCase,
)
from app.infrastructure.notifications.booking_notifier import SMTPBookingNotifier
from app.infrastructure.persistence.repositories.booking import (
    SQLAlchemyBookingRepository,
)
from app.infrastructure.persistence.repositories.service import (
    SQLAlchemyServiceRepository,
)

router = APIRouter()


# ── Públicos ───────────────────────────────────────────────────────────────────


@router.get("/disponibilidad", response_model=DisponibilidadOut)
def get_disponibilidad(
    fecha: date = Query(..., description="Fecha en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _rl: None = Depends(limiter(max_requests=30, window_seconds=60)),
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
def crear_reserva(
    data: BookingCreate,
    db: Session = Depends(get_db),
    _rl: None = Depends(limiter(max_requests=10, window_seconds=60)),
):
    """
    Crea una reserva (acceso público — el cliente la solicita desde la web).
    Devuelve 409 si ya existe una cita activa en esa fecha+hora.
    """
    service_repo = SQLAlchemyServiceRepository(db)
    service = service_repo.get_by_id(data.servicio_id)
    if not service or not service.activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El servicio {data.servicio_id} no existe o no está disponible.",
        )

    booking = Booking(
        nombre_cliente=data.nombre_cliente,
        telefono=data.telefono,
        email=data.email,
        servicio_id=service.id,
        servicio_nombre=service.nombre,
        fecha_hora=data.fecha_hora,
        barbero=data.barbero or DEFAULT_BARBER,
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


@router.get("/", response_model=PagedResponse[BookingOut])
def listar_reservas(
    estado: Optional[str] = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """Lista reservas paginadas. Solo accesible para el admin."""
    repo = SQLAlchemyBookingRepository(db)
    uc = ListBookingsUseCase(repo)
    items, total = uc.execute(estado=estado, skip=pagination.skip, limit=pagination.limit)
    return PagedResponse(
        items=[BookingOut.model_validate(b) for b in items],
        total=total,
        page=pagination.page,
        size=pagination.size,
        pages=pagination.total_pages(total),
    )


@router.get("/export", response_class=StreamingResponse)
def exportar_reservas_csv(
    desde: date = Query(..., description="Fecha inicio del rango (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha fin del rango (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """
    Descarga un CSV con todas las reservas en el rango [desde, hasta] (ambos inclusive).

    Columnas: id, nombre_cliente, telefono, servicio, fecha_hora, estado, creada_en.
    Solo accesible para el admin.
    """
    repo = SQLAlchemyBookingRepository(db)
    uc = ExportBookingsCSVUseCase(repo)
    try:
        bookings = uc.execute(desde, hasta)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return _build_csv_response(bookings, desde, hasta)


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


def _build_csv_response(
    bookings: list[Booking],
    desde: date,
    hasta: date,
) -> StreamingResponse:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(
        ["id", "nombre_cliente", "telefono", "servicio", "fecha_hora", "estado", "creada_en"]
    )
    for b in bookings:
        writer.writerow(
            [
                b.id,
                b.nombre_cliente,
                b.telefono,
                b.servicio_nombre or "",
                b.fecha_hora.strftime("%Y-%m-%d %H:%M"),
                b.estado,
                b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
            ]
        )
    buf.seek(0)
    filename = f"reservas_{desde}_{hasta}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
