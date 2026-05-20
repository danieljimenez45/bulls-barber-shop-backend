"""
Rutas del panel de administrador.
Todas requieren JWT válido — solo accesibles para Jonathan.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_admin
from app.api.schemas.stats import StatsOut
from app.database import get_db
from app.domain.auth.entity import AdminUser
from app.domain.stats.use_cases import GetStatsUseCase
from app.infrastructure.persistence.repositories.stats import (
    SQLAlchemyStatsRepository,
)

router = APIRouter()


@router.get("/stats", response_model=StatsOut)
def obtener_estadisticas(
    db: Session = Depends(get_db),
    _admin: AdminUser = Depends(get_current_admin),
):
    """
    Estadísticas del negocio para el dashboard del administrador.

    Devuelve:
    - Número de citas hoy / esta semana / este mes (excluye canceladas)
    - Ingresos estimados semana / mes (suma precios en citas confirmadas o completadas)
    - Top 5 servicios más solicitados
    - Distribución de citas por estado
    - Próxima cita pendiente o confirmada
    """
    repo = SQLAlchemyStatsRepository(db)
    uc = GetStatsUseCase(repo)
    snapshot = uc.execute()

    # Traducción manual porque StatsSnapshot contiene listas de dataclasses
    return StatsOut(
        citas_hoy=snapshot.citas_hoy,
        citas_semana=snapshot.citas_semana,
        citas_mes=snapshot.citas_mes,
        ingresos_estimados_semana=snapshot.ingresos_estimados_semana,
        ingresos_estimados_mes=snapshot.ingresos_estimados_mes,
        servicios_mas_solicitados=[
            {"servicio_id": s.servicio_id, "nombre": s.nombre, "total": s.total}
            for s in snapshot.servicios_mas_solicitados
        ],
        distribucion_por_estado=snapshot.distribucion_por_estado,
        proxima_cita=(
            {
                "id": snapshot.proxima_cita.id,
                "nombre_cliente": snapshot.proxima_cita.nombre_cliente,
                "telefono": snapshot.proxima_cita.telefono,
                "fecha_hora": snapshot.proxima_cita.fecha_hora,
                "servicio_nombre": snapshot.proxima_cita.servicio_nombre,
                "estado": snapshot.proxima_cita.estado,
            }
            if snapshot.proxima_cita
            else None
        ),
    )
