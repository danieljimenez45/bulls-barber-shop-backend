from typing import List, Optional

from pydantic import ConfigDict, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Bulls Barber Shop"
    # Seguro por defecto: DEBUG=False en producción.
    # En desarrollo pon DEBUG=true en tu .env local.
    DEBUG: bool = False

    # Base de datos (SQLite para dev, PostgreSQL para producción)
    DATABASE_URL: str = "sqlite:///./bulls_barbershop.db"

    # ── Seguridad — JWT ───────────────────────────────────────────────────────
    # SECRET_KEY no tiene valor por defecto en el código.
    # Debe configurarse siempre mediante variable de entorno o fichero .env.
    # Genera un valor seguro con: openssl rand -hex 32
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 h

    @model_validator(mode="after")
    def validate_secret_key(self) -> "Settings":
        """Impide arrancar sin SECRET_KEY configurada."""
        if not self.SECRET_KEY:
            raise ValueError(
                "SECRET_KEY no está configurada. "
                "Define la variable de entorno SECRET_KEY o añádela a tu fichero .env. "
                "Genera un valor seguro con: openssl rand -hex 32"
            )
        return self

    # CORS — orígenes permitidos.
    # En .env se puede definir como JSON o lista separada por comas:
    #   CORS_ORIGINS=["https://bullsbarbershop.es","https://www.bullsbarbershop.es"]
    #   CORS_ORIGINS=https://bullsbarbershop.es,https://www.bullsbarbershop.es
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Dominio de producción (se añade automáticamente a CORS_ORIGINS en prod)
    PRODUCTION_DOMAIN: str = ""

    # Rate limiting — se puede deshabilitar en dev poniendo RATE_LIMIT_ENABLED=false
    RATE_LIMIT_ENABLED: bool = True

    # Email (para notificaciones de reservas — opcional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    ADMIN_EMAIL: str = ""

    # Cloudinary — almacenamiento de imágenes en la nube (B-26)
    # Si los tres valores están configurados se usa Cloudinary.
    # Si alguno está vacío, se usa el almacenamiento local (dev).
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    # Carpeta dentro de tu cuenta Cloudinary donde se organizarán las imágenes
    CLOUDINARY_FOLDER: str = "bulls_barbershop"

    @property
    def cloudinary_enabled(self) -> bool:
        """True cuando las credenciales de Cloudinary están completas."""
        return bool(
            self.CLOUDINARY_CLOUD_NAME
            and self.CLOUDINARY_API_KEY
            and self.CLOUDINARY_API_SECRET
        )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Acepta string JSON, lista separada por comas o lista nativa."""
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def get_cors_origins(self) -> List[str]:
        """Devuelve los orígenes CORS incluyendo el dominio de producción si está configurado."""
        origins = list(self.CORS_ORIGINS)
        if self.PRODUCTION_DOMAIN:
            domain = self.PRODUCTION_DOMAIN.rstrip("/")
            for scheme in ("https://", "http://"):
                candidate = f"{scheme}{domain.removeprefix('https://').removeprefix('http://')}"
                if candidate not in origins:
                    origins.append(candidate)
        return origins

    model_config = ConfigDict(env_file=".env")


settings = Settings()
