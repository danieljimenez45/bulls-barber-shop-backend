from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin, get_optional_admin
from app.api.schemas.service import ServiceCreate, ServiceOut, ServiceUpdate
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.service.entity import Service
from app.domain.service.ports import ServiceNotFound
from app.domain.service.use_cases import (
    CreateServiceUseCase,
    DeleteServiceUseCase,
    GetServiceUseCase,
    ListServicesUseCase,
    UpdateServiceUseCase,
)
from app.infrastructure.persistence.repositories.service import (
    SQLAlchemyServiceRepository,
)

router = APIRouter()


# ── Públicos ───────────────────────────────────────────────────────────────────


@router.get("/", response_model=List[ServiceOut])
def listar_servicios(
    categoria: Optional[str] = None,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    admin: AdminUser | None = Depends(get_optional_admin),
):
    """Devuelve servicios filtrados por categoría.

    - Público (sin token): solo devuelve servicios activos (solo_activos=true forzado).
    - Admin (con JWT válido): puede solicitar solo_activos=false para ver los inactivos.

    Cualquier intento de pasar solo_activos=false sin JWT válido devuelve 401.
    """
    if not solo_activos and admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere autenticación para listar servicios inactivos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = SQLAlchemyServiceRepository(db)
    uc = ListServicesUseCase(repo)
    services = uc.execute(solo_activos=solo_activos, categoria=categoria)
    return [ServiceOut.model_validate(s) for s in services]


@router.get("/{service_id}", response_model=ServiceOut)
def obtener_servicio(service_id: int, db: Session = Depends(get_db)):
    repo = SQLAlchemyServiceRepository(db)
    uc = GetServiceUseCase(repo)
    try:
        service = uc.execute(service_id)
        return ServiceOut.model_validate(service)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ── Protegidos (solo admin) ────────────────────────────────────────────────────


@router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def crear_servicio(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    service = Service(
        nombre=data.nombre,
        descripcion=data.descripcion,
        precio=data.precio,
        duracion_minutos=data.duracion_minutos,
        categoria=data.categoria,
        imagen_url=data.imagen_url,
        activo=data.activo,
        orden=data.orden,
    )
    repo = SQLAlchemyServiceRepository(db)
    uc = CreateServiceUseCase(repo)
    created = uc.execute(service)
    return ServiceOut.model_validate(created)


@router.put("/{service_id}", response_model=ServiceOut)
def actualizar_servicio(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyServiceRepository(db)
    uc = UpdateServiceUseCase(repo)
    try:
        updated = uc.execute(service_id, **data.model_dump(exclude_unset=True))
        return ServiceOut.model_validate(updated)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servicio(
    service_id: int,
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    repo = SQLAlchemyServiceRepository(db)
    uc = DeleteServiceUseCase(repo)
    try:
        uc.execute(service_id)
    except ServiceNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc))
