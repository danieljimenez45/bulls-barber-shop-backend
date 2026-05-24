"""
cloudinary_storage.py
──────────────────────────────────────────────────────────────────────────────
Adaptador Cloudinary que implementa el puerto IFileStorage.

Por qué Cloudinary:
  - Las imágenes se sirven desde la CDN global de Cloudinary, no desde el
    servidor de la app → menor carga, mayor velocidad para el cliente.
  - Persistencia real: las imágenes sobreviven reinicios, redespliegues y
    cambios de servidor (problema fundamental del almacenamiento local en
    entornos cloud/Docker).
  - Transformaciones automáticas (redimensionado, compresión, WebP) sin
    código adicional.

Funcionamiento:
  - save()   → sube el fichero como un stream de bytes; devuelve la URL HTTPS
               pública entregada por Cloudinary (se guarda en BD como imagen_url).
  - delete() → extrae el public_id de la URL de Cloudinary y borra el asset.

Compatibilidad con el puerto IFileStorage:
  La firma de ambos métodos es idéntica a LocalFileStorage, por lo que el
  router y los casos de uso no necesitan ningún cambio.
──────────────────────────────────────────────────────────────────────────────
"""

import io
import os
from urllib.parse import urlparse

import cloudinary
import cloudinary.uploader

from app.domain.gallery.ports import IFileStorage


class CloudinaryFileStorage(IFileStorage):
    """
    Implementación de IFileStorage que persiste imágenes en Cloudinary.

    Parámetros
    ----------
    cloud_name : str
        Nombre del cloud de Cloudinary (CLOUDINARY_CLOUD_NAME).
    api_key : str
        Clave de API (CLOUDINARY_API_KEY).
    api_secret : str
        Secreto de API (CLOUDINARY_API_SECRET).
    folder : str
        Carpeta virtual dentro de Cloudinary donde se almacenarán las imágenes.
        Por defecto "bulls_barbershop".
    """

    def __init__(
        self,
        cloud_name: str,
        api_key: str,
        api_secret: str,
        folder: str = "bulls_barbershop",
    ) -> None:
        # Configuramos el SDK de Cloudinary con las credenciales recibidas.
        # La configuración es global al proceso (singleton del SDK), pero al
        # llamarla cada vez nos aseguramos de que está actualizada.
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,  # siempre URLs HTTPS
        )
        self._folder = folder

    # ── IFileStorage ──────────────────────────────────────────────────────────

    def save(self, file_data: bytes, extension: str) -> str:
        """
        Sube el fichero a Cloudinary y devuelve su URL pública HTTPS.

        La URL tiene el formato:
            https://res.cloudinary.com/{cloud}/{image/upload}/{public_id}.{ext}

        Esta URL se almacena directamente en la columna `imagen_url` de la BD,
        y el frontend la usa como atributo `src` de <img>.  Cloudinary sirve
        la imagen desde su CDN global sin pasar por el servidor de la app.

        Raises
        ------
        ValueError
            Si la extensión no está en ALLOWED_EXTENSIONS.
        RuntimeError
            Si Cloudinary devuelve un error durante la subida.
        """
        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Extensión '{extension}' no permitida. "
                f"Usa una de: {sorted(self.ALLOWED_EXTENSIONS)}"
            )

        # Mapeamos la extensión al formato que entiende Cloudinary
        fmt = extension.lstrip(".").lower()
        if fmt == "jpg":
            fmt = "jpeg"

        try:
            result = cloudinary.uploader.upload(
                io.BytesIO(file_data),
                folder=self._folder,
                resource_type="image",
                format=fmt,
                # Limitamos el tamaño máximo a 10 MB en el lado servidor también
                chunk_size=6_000_000,
            )
        except cloudinary.exceptions.Error as exc:
            raise RuntimeError(f"Error al subir imagen a Cloudinary: {exc}") from exc

        secure_url: str = result["secure_url"]
        return secure_url

    def delete(self, url_path: str) -> None:
        """
        Elimina la imagen de Cloudinary extrayendo el public_id de la URL.

        El public_id en Cloudinary incluye la carpeta pero NO la extensión:
            URL:       https://res.cloudinary.com/mycloud/image/upload/v123/bulls_barbershop/abc.jpg
            public_id: bulls_barbershop/abc

        Si la URL no pertenece a Cloudinary (p.ej. imágenes locales antiguas
        durante la migración) el método lo ignora silenciosamente para no
        romper el flujo de borrado.
        """
        public_id = self._extract_public_id(url_path)
        if not public_id:
            return  # URL local o inválida — nada que borrar en Cloudinary

        try:
            cloudinary.uploader.destroy(public_id, resource_type="image")
        except cloudinary.exceptions.Error:
            # Logueamos pero no propagamos: si el fichero ya no existe en
            # Cloudinary no queremos que el borrado del registro en BD falle.
            pass

    # ── Helpers privados ──────────────────────────────────────────────────────

    @staticmethod
    def _extract_public_id(url: str) -> str:
        """
        Extrae el public_id de una URL de Cloudinary.

        Ejemplo:
            entrada:  https://res.cloudinary.com/mycloud/image/upload/v1234/bulls_barbershop/abc.jpg
            salida:   bulls_barbershop/abc

        Devuelve cadena vacía si la URL no es de Cloudinary o no se puede parsear.
        """
        if "cloudinary.com" not in url:
            return ""

        try:
            path = urlparse(url).path
            # path → /mycloud/image/upload/v1234567890/bulls_barbershop/abc.jpg
            parts = path.strip("/").split("/")

            # Buscamos el segmento 'upload' para saber dónde empieza el public_id
            upload_idx = parts.index("upload")
            remaining = parts[upload_idx + 1 :]

            # Saltamos el número de versión (empieza por 'v' seguido de dígitos)
            if remaining and remaining[0].startswith("v") and remaining[0][1:].isdigit():
                remaining = remaining[1:]

            # Unimos los segmentos restantes y quitamos la extensión
            public_id_with_ext = "/".join(remaining)
            public_id, _ = os.path.splitext(public_id_with_ext)
            return public_id

        except (ValueError, IndexError):
            return ""
