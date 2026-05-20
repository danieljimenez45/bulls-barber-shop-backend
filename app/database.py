from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# Para SQLite necesitamos check_same_thread=False
connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependencia de FastAPI para inyectar la sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Crea todas las tablas al arrancar la app."""
    # Importamos los ORM models para que SQLAlchemy los registre en la metadata
    from app.infrastructure.persistence.orm import (  # noqa: F401
        booking,
        gallery,
        review,
        service,
        user,
    )

    Base.metadata.create_all(bind=engine)
