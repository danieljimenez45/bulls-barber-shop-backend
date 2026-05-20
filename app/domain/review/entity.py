from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Review:
    nombre: str
    valoracion: int
    id: Optional[int] = None
    comentario: Optional[str] = None
    visible: bool = True
    created_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not 1 <= self.valoracion <= 5:
            raise ValueError("La valoración debe estar entre 1 y 5")

    def mostrar(self) -> None:
        self.visible = True

    def ocultar(self) -> None:
        self.visible = False
