import math
from fastapi import Query


class PaginationParams:
    """Dependencia de FastAPI que extrae y normaliza page/size desde query params."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Número de página (desde 1)"),
        size: int = Query(20, ge=1, le=100, description="Resultados por página (máx. 100)"),
    ) -> None:
        self.page = page
        self.size = size
        self.skip = (page - 1) * size
        self.limit = size

    def total_pages(self, total: int) -> int:
        return max(1, math.ceil(total / self.size))
