import os
import uuid

from app.domain.gallery.ports import IFileStorage

_UPLOAD_DIR = "uploads/gallery"


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
        return f"/uploads/gallery/{filename}"

    def delete(self, url_path: str) -> None:
        local_path = url_path.lstrip("/")
        if os.path.exists(local_path):
            os.remove(local_path)
