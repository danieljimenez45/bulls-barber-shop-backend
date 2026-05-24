"""
alembic/env.py
──────────────────────────────────────────────────────────────────────────────
Entorno de ejecución de Alembic para Bulls Barber Shop.

Responsabilidades:
  1. Añadir el directorio raíz al sys.path para que `app.*` sea importable.
  2. Inyectar la DATABASE_URL real desde app.config.settings (sobreescribe el
     placeholder de alembic.ini, de modo que funciona con SQLite en dev y
     PostgreSQL en producción sin cambiar ningún fichero de configuración).
  3. Registrar todos los modelos ORM en Base.metadata importándolos aquí
     (Alembic los necesita para --autogenerate y para detectar diffs).
  4. Exponer target_metadata y las dos funciones estándar de Alembic:
     run_migrations_offline() y run_migrations_online().
──────────────────────────────────────────────────────────────────────────────
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ── 1. Aseguramos que `app` sea importable ────────────────────────────────────
# alembic/env.py vive en backend/alembic/; el paquete `app` está en backend/app/
# → subimos un nivel para llegar a backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── 2. Importamos settings para obtener la URL de la BD ──────────────────────
from app.config import settings  # noqa: E402

# ── 3. Importamos Base y todos los modelos ORM ────────────────────────────────
# Base debe importarse ANTES que los modelos para que la metadata esté lista.
from app.database import Base  # noqa: E402
from app.infrastructure.persistence.orm import (  # noqa: E402, F401
    booking,         # → tabla bookings
    contact,         # → tabla contact_messages  (B-24)
    gallery,         # → tabla gallery
    review,          # → tabla reviews
    service,         # → tabla services
    user,            # → tabla admin_users
)

# ── Configuración de Alembic ──────────────────────────────────────────────────
config = context.config

# Sobreescribimos la URL con el valor real de la aplicación
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configuramos el logging de Python según el [loggers] de alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadatos objetivo para --autogenerate
target_metadata = Base.metadata


# ── Migraciones en modo OFFLINE ───────────────────────────────────────────────
def run_migrations_offline() -> None:
    """
    Ejecuta las migraciones usando solo la URL (sin conexión activa).
    Útil para generar SQL sin acceso a la BD (p.ej. para revisión o CI).
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,          # detecta cambios de tipo de columna
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Migraciones en modo ONLINE ────────────────────────────────────────────────
def run_migrations_online() -> None:
    """
    Ejecuta las migraciones con una conexión activa a la BD.
    Es el modo habitual cuando se lanza desde la app o desde la CLI.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # sin pool: cada migración abre/cierra conexión
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


# ── Punto de entrada ──────────────────────────────────────────────────────────
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
