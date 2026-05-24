"""
app/infrastructure/storage/__init__.py
──────────────────────────────────────────────────────────────────────────────
Fábrica de almacenamiento de ficheros.

Expone una única función pública: get_file_storage()

Lógica de selección:
  - Si las tres variables de Cloudinary (CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET) están configuradas → CloudinaryFileStorage
  - En cualquier otro caso → LocalFileStorage  (modo dev / fallback)

Esto permite que el código que consume el puerto IFileStorage (el router de
galería) no necesite saber en qué entorno está corriendo.  Al hacer el
despliegue solo hay que añadir las variables de entorno al servidor.
──────────────────────────────────────────────────────────────────────────────
"""

from app.config import settings
from app.domain.gallery.ports import IFileStorage


def get_file_storage() -> IFileStorage:
    """
    Devuelve la implementación de IFileStorage adecuada para el entorno actual.

    Uso:
        storage = get_file_storage()
        url = storage.save(file_bytes, ".jpg")

    Dev  → LocalFileStorage  (guarda en uploads/gallery/)
    Prod → CloudinaryFileStorage (sube a Cloudinary CDN)
    """
    if settings.cloudinary_enabled:
        from app.infrastructure.storage.cloudinary_storage import CloudinaryFileStorage

        return CloudinaryFileStorage(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            folder=settings.CLOUDINARY_FOLDER,
        )

    from app.infrastructure.storage.local import LocalFileStorage

    return LocalFileStorage()
