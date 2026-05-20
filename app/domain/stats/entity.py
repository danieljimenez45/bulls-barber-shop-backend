from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ServicioStat:
    """Estadística de un servicio: cuántas veces ha sido solicitado."""

    servicio_id: int
    nombre: Optional[str]
    total: int


@dataclass
class ProximaCita:
    """Datos esenciales de la próxima cita pendiente o confirmada."""

    id: int
    nombre_cliente: str
    telefono: str
    fecha_hora: datetime
    servicio_nombre: Optional[str]
    estado: str


@dataclass
class StatsSnapshot:
    """Instantánea de estadísticas del negocio para el dashboard del admin."""

    # Volumen de citas
    citas_hoy: int
    citas_semana: int
    citas_mes: int

    # Ingresos estimados (suma de precios de servicios en citas confirmadas/completadas)
    ingresos_estimados_semana: float
    ingresos_estimados_mes: float

    # Rankings y distribución
    servicios_mas_solicitados: List[ServicioStat] = field(default_factory=list)
    distribucion_por_estado: Dict[str, int] = field(default_factory=dict)

    # Siguiente cita en agenda
    proxima_cita: Optional[ProximaCita] = None
