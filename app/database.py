import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

# ── SQLite: activar comprobación de FK en cada conexión ───────────────────────
# SQLite deshabilita las FK por defecto por compatibilidad con versiones antiguas.
# El listener se registra a nivel de clase (Engine), por lo que afecta a TODOS
# los engines del proceso, incluido el engine de test creado en conftest.py.
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


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


def run_migrations() -> None:
    """
    B-25 — Aplica las migraciones Alembic pendientes.

    Equivale a ejecutar `alembic upgrade head` desde la línea de comandos.
    Es seguro llamarlo cada vez que arranca la app: si la BD ya está en la
    última revisión, Alembic lo detecta y no hace nada.

    Para bases de datos existentes (creadas con create_tables() antes de B-25):
        alembic stamp 0001
    Esto marca la BD como ya migrada sin re-ejecutar la migración inicial.
    """
    import os

    from alembic import command
    from alembic.config import Config

    # alembic.ini vive en el mismo directorio que este módulo sube dos niveles:
    # app/database.py → app/ → backend/   →   backend/alembic.ini
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def create_tables() -> None:
    """
    DEPRECATED — Crea las tablas directamente con SQLAlchemy create_all().

    Mantenido como fallback de emergencia.  En producción se usa run_migrations()
    (Alembic) que gestiona el historial de cambios de esquema.
    """
    # Importamos los ORM models para que SQLAlchemy los registre en la metadata
    from app.infrastructure.persistence.orm import (  # noqa: F401
        booking,
        contact,   # B-24: mensajes de contacto
        gallery,
        review,
        service,
        user,
    )

    Base.metadata.create_all(bind=engine)
