from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Bulls Barber Shop"
    DEBUG: bool = True

    # Base de datos (SQLite para dev, PostgreSQL para producción)
    DATABASE_URL: str = "sqlite:///./bulls_barbershop.db"

    # Seguridad — JWT
    SECRET_KEY: str = "changeme-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 h (adecuado para tablet en barbería)

    # CORS — orígenes permitidos
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # Email (para notificaciones de reservas — opcional)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
