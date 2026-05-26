import os
import uuid
from pathlib import Path

from app.domain.gallery.ports import IFileStorage

_UPLOAD_DIR = "uploads/gallery"
_BASE_DIR = Path(_UPLOAD_DIR).resolve()
_URL_PREFIX = "/uploads/gallery/"


class LocalFileStorage(IFileStorage):
    """Almacena imágenes en el sistema de ficheros local."""

    def __init__(self, upload_dir: str = _UPLOAD_DIR) -> None:
        self._upload_dir = upload_dir
        os.makedirs(self._upload_dir, exist_ok=True)

    def save(self, file_data: bytes, extension: str) -> str:
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Extensión '{extension}' no permitida. "
                f"Usa una de: {sorted(self.ALLOWED_EXTENSIONS)}"
            )
        filename = f"{uuid.uuid4().hex}{extension}"
        filepath = os.path.join(self._upload_dir, filename)
        with open(filepath, "wb") as f:
            f.write(file_data)
        return f"{_URL_PREFIX}{filename}"

    def delete(self, url_path: str) -> None:
        if not url_path.startswith(_URL_PREFIX):
            raise ValueError("Ruta de fichero no permitida")

        rel = url_path[len(_URL_PREFIX) :].lstrip("/")
        target = (_BASE_DIR / rel).resolve()

        try:
            target.relative_to(_BASE_DIR)
        except ValueError:
            raise ValueError("Ruta de fichero no permitida") from None

        if target.is_file():
            target.unlink()
