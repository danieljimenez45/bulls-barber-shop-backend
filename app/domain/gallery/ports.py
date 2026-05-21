from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.gallery.entity import GalleryImage


class ImageNotFound(Exception):
    """Se lanza cuando no se encuentra una imagen por su ID."""


class IGalleryRepository(ABC):

    @abstractmethod
    def add(self, image: GalleryImage) -> GalleryImage: ...

    @abstractmethod
    def get_by_id(self, image_id: int) -> Optional[GalleryImage]: ...

    @abstractmethod
    def list(
        self,
        categoria: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[GalleryImage]: ...

    @abstractmethod
    def count(self, categoria: Optional[str] = None) -> int: ...

    @abstractmethod
    def delete(self, image_id: int) -> None: ...


class IFileStorage(ABC):
    """Puerto para persistencia de ficheros binarios (imágenes)."""

    ALLOWED_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})

    @abstractmethod
    def save(self, file_data: bytes, extension: str) -> str:
        """Guarda el fichero y devuelve la URL pública relativa."""

    @abstractmethod
    def delete(self, url_path: str) -> None:
        """Elimina el fichero del almacenamiento."""
