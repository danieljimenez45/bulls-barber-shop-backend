"""Esquema inicial — 6 tablas del dominio

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000

Tablas creadas:
  - admin_users        (autenticación del panel)
  - services           (catálogo de servicios)
  - bookings           (reservas con soft-delete B-22)
  - reviews            (reseñas de clientes)
  - gallery            (imágenes de la galería)
  - contact_messages   (mensajes del formulario de contacto B-24)

NOTA para bases de datos existentes (antes de añadir Alembic):
  Si ya tienes la BD en uso, márcala como migrada sin re-crear las tablas:
      alembic stamp 0001
  Después, las migraciones futuras se aplicarán normalmente con:
      alembic upgrade head
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ── Identificadores de revisión ───────────────────────────────────────────────
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea todas las tablas del esquema inicial."""

    # ── admin_users ────────────────────────────────────────────────────────────
    op.create_table(
        "admin_users",
        sa.Column("id",              sa.Integer(),     primary_key=True),
        sa.Column("email",           sa.String(255),   nullable=False),
        sa.Column("hashed_password", sa.String(255),   nullable=False),
        sa.Column("is_active",       sa.Boolean(),     nullable=True,  server_default=sa.text("1")),
        sa.Column("created_at",      sa.DateTime(),    nullable=True,  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("email", name="uq_admin_users_email"),
    )
    op.create_index("ix_admin_users_id",    "admin_users", ["id"],    unique=False)
    op.create_index("ix_admin_users_email", "admin_users", ["email"], unique=True)

    # ── services ───────────────────────────────────────────────────────────────
    op.create_table(
        "services",
        sa.Column("id",               sa.Integer(),     primary_key=True),
        sa.Column("nombre",           sa.String(100),   nullable=False),
        sa.Column("descripcion",      sa.Text(),        nullable=True),
        sa.Column("precio",           sa.Float(),       nullable=False),
        sa.Column("duracion_minutos", sa.Integer(),     nullable=True,  server_default=sa.text("30")),
        sa.Column("categoria",        sa.String(50),    nullable=True,  server_default=sa.text("'corte'")),
        sa.Column("imagen_url",       sa.String(255),   nullable=True),
        sa.Column("activo",           sa.Boolean(),     nullable=True,  server_default=sa.text("1")),
        sa.Column("orden",            sa.Integer(),     nullable=True,  server_default=sa.text("0")),
    )
    op.create_index("ix_services_id", "services", ["id"], unique=False)

    # ── bookings ───────────────────────────────────────────────────────────────
    # deleted_at = NULL → reserva activa; timestamp → soft-deleted (B-22)
    op.create_table(
        "bookings",
        sa.Column("id",              sa.Integer(),     primary_key=True),
        sa.Column("nombre_cliente",  sa.String(100),   nullable=False),
        sa.Column("telefono",        sa.String(20),    nullable=False),
        sa.Column("email",           sa.String(100),   nullable=True),
        sa.Column("servicio_id",     sa.Integer(),     nullable=False),
        sa.Column("servicio_nombre", sa.String(100),   nullable=True),
        sa.Column("fecha_hora",      sa.DateTime(),    nullable=False),
        sa.Column("barbero",         sa.String(100),   nullable=True,  server_default=sa.text("'Cualquier barbero'")),
        sa.Column("notas",           sa.Text(),        nullable=True),
        sa.Column("estado",          sa.String(20),    nullable=True,  server_default=sa.text("'pendiente'")),
        sa.Column("created_at",      sa.DateTime(),    nullable=True,  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("deleted_at",      sa.DateTime(),    nullable=True),  # B-22
    )
    op.create_index("ix_bookings_id", "bookings", ["id"], unique=False)

    # ── reviews ────────────────────────────────────────────────────────────────
    op.create_table(
        "reviews",
        sa.Column("id",         sa.Integer(),   primary_key=True),
        sa.Column("nombre",     sa.String(100), nullable=False),
        sa.Column("valoracion", sa.Integer(),   nullable=False),
        sa.Column("comentario", sa.Text(),      nullable=True),
        sa.Column("visible",    sa.Boolean(),   nullable=True,  server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(),  nullable=True,  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_reviews_id", "reviews", ["id"], unique=False)

    # ── gallery ────────────────────────────────────────────────────────────────
    op.create_table(
        "gallery",
        sa.Column("id",          sa.Integer(),   primary_key=True),
        sa.Column("titulo",      sa.String(100), nullable=True),
        sa.Column("descripcion", sa.Text(),      nullable=True),
        sa.Column("imagen_url",  sa.String(255), nullable=False),
        sa.Column("categoria",   sa.String(50),  nullable=True,  server_default=sa.text("'corte'")),
        sa.Column("visible",     sa.Boolean(),   nullable=True,  server_default=sa.text("1")),
        sa.Column("orden",       sa.Integer(),   nullable=True,  server_default=sa.text("0")),
        sa.Column("created_at",  sa.DateTime(),  nullable=True,  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_gallery_id", "gallery", ["id"], unique=False)

    # ── contact_messages ───────────────────────────────────────────────────────
    # B-24: persistencia de mensajes del formulario de contacto
    op.create_table(
        "contact_messages",
        sa.Column("id",         sa.Integer(),    primary_key=True),
        sa.Column("nombre",     sa.String(100),  nullable=False),
        sa.Column("email",      sa.String(150),  nullable=False),
        sa.Column("telefono",   sa.String(20),   nullable=True),
        sa.Column("asunto",     sa.String(200),  nullable=True),
        sa.Column("mensaje",    sa.Text(),        nullable=False),
        sa.Column("leido",      sa.Boolean(),    nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(),   nullable=True,  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_contact_messages_id", "contact_messages", ["id"], unique=False)


def downgrade() -> None:
    """Elimina todas las tablas del esquema inicial (orden inverso por dependencias)."""
    op.drop_table("contact_messages")
    op.drop_table("gallery")
    op.drop_table("reviews")
    op.drop_table("bookings")
    op.drop_table("services")
    op.drop_table("admin_users")
