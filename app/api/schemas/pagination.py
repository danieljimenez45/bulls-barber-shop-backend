from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PagedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica reutilizable en cualquier endpoint de listado."""

    items: List[T]
    total: int   # total de registros que coinciden con los filtros
    page: int    # página actual (desde 1)
    size: int    # resultados por página solicitados
    pages: int   # número total de páginas
