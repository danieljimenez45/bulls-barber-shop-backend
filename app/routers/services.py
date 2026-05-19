from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.service import Service
from app.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate

router = APIRouter()


@router.get("/", response_model=List[ServiceOut])
def listar_servicios(
    categoria: Optional[str] = None,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
):
    """Devuelve todos los servicios, filtrados opcionalmente por categoría."""
    query = db.query(Service)
    if solo_activos:
        query = query.filter(Service.activo == True)  # noqa: E712
    if categoria:
        query = query.filter(Service.categoria == categoria)
    return query.order_by(Service.orden).all()


@router.get("/{service_id}", response_model=ServiceOut)
def obtener_servicio(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    return service


@router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def crear_servicio(data: ServiceCreate, db: Session = Depends(get_db)):
    service = Service(**data.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.put("/{service_id}", response_model=ServiceOut)
def actualizar_servicio(
    service_id: int, data: ServiceUpdate, db: Session = Depends(get_db)
):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servicio(service_id: int, db: Session = Depends(get_db)):
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")
    db.delete(service)
    db.commit()
