from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Booking:
    nombre_cliente: str
    telefono: str
    servicio_id: int
    fecha_hora: datetime
    id: Optional[int] = None
    email: Optional[str] = None
    servicio_nombre: Optional[str] = None
    barbero: str = "Cualquier barbero"
    notas: Optional[str] = None
    estado: str = "pendiente"
    created_at: Optional[datetime] = None

    ESTADOS_VALIDOS = frozenset({"pendiente", "confirmada", "cancelada", "completada"})

    def confirmar(self) -> None:
        self.estado = "confirmada"

    def cancelar(self) -> None:
        self.estado = "cancelada"

    def completar(self) -> None:
        self.estado = "completada"

    def cambiar_estado(self, nuevo_estado: str) -> None:
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado '{nuevo_estado}' no válido. "
                f"Usa uno de: {sorted(self.ESTADOS_VALIDOS)}"
            )
        self.estado = nuevo_estado
