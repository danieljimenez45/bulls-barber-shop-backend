from typing import List, Optional, Tuple

from app.domain.gallery.entity import GalleryImage
from app.domain.gallery.ports import IGalleryRepository, IFileStorage, ImageNotFound


class ListImagesUseCase:
    def __init__(self, repo: IGalleryRepository) -> None:
        self._repo = repo

    def execute(
        self,
        categoria: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> Tuple[List[GalleryImage], int]:
        items = self._repo.list(categoria=categoria, skip=skip, limit=limit)
        total = self._repo.count(categoria=categoria)
        return items, total


class UploadImageUseCase:
    def __init__(self, repo: IGalleryRepository, storage: IFileStorage) -> None:
        self._repo = repo
        self._storage = storage

    def execute(
        self,
        file_data: bytes,
        extension: str,
        titulo: Optional[str] = None,
        categoria: str = "corte",
    ) -> GalleryImage:
        url = self._storage.save(file_data, extension)
        image = GalleryImage(imagen_url=url, titulo=titulo, categoria=categoria)
        return self._repo.add(image)


class DeleteImageUseCase:
    def __init__(self, repo: IGalleryRepository, storage: IFileStorage) -> None:
        self._repo = repo
        self._storage = storage

    def execute(self, image_id: int) -> None:
        image = self._repo.get_by_id(image_id)
        if not image:
            raise ImageNotFound(f"Imagen {image_id} no encontrada")
        self._storage.delete(image.imagen_url)
        self._repo.delete(image_id)
