from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class ServicioStatOut(BaseModel):
    servicio_id: int
    nombre: Optional[str] = None
    total: int

    model_config = {"from_attributes": True}


class ProximaCitaOut(BaseModel):
    id: int
    nombre_cliente: str
    telefono: str
    fecha_hora: datetime
    servicio_nombre: Optional[str] = None
    estado: str

    model_config = {"from_attributes": True}


class StatsOut(BaseModel):
    # Volumen de citas
    citas_hoy: int
    citas_semana: int
    citas_mes: int

    # Ingresos estimados (€)
    ingresos_estimados_semana: float
    ingresos_estimados_mes: float

    # Rankings y distribución
    servicios_mas_solicitados: List[ServicioStatOut]
    distribucion_por_estado: Dict[str, int]

    # Próxima cita en agenda
    proxima_cita: Optional[ProximaCitaOut] = None

    model_config = {"from_attributes": True}
