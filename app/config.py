from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Bulls Barber Shop"
    DEBUG: bool = True

    # Base de datos (SQLite para dev, PostgreSQL para producción)
    DATABASE_URL: str = "sqlite:///./bulls_barbershop.db"

    # Seguridad — JWT
    SECRET_KEY: str = "changeme-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 h

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

    # Email (para notificaciones de reservas — opcional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""
    ADMIN_EMAIL: str = ""

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

    class Config:
        env_file = ".env"


settings = Settings()
