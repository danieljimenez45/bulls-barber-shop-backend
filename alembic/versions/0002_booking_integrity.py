"""Índice único parcial para slots de reserva activos

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-25

Garantiza un solo booking pendiente/confirmada por fecha_hora (sin soft-delete).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ACTIVE_SLOT_WHERE = (
    "deleted_at IS NULL AND estado IN ('pendiente', 'confirmada')"
)


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.create_index(
            "uq_bookings_slot_active",
            "bookings",
            ["fecha_hora"],
            unique=True,
            postgresql_where=sa.text(_ACTIVE_SLOT_WHERE),
        )
    else:
        # SQLite 3.8+ — índice parcial equivalente
        op.create_index(
            "uq_bookings_slot_active",
            "bookings",
            ["fecha_hora"],
            unique=True,
            sqlite_where=sa.text(_ACTIVE_SLOT_WHERE),
        )

    op.create_index(
        "ix_bookings_fecha_hora_deleted",
        "bookings",
        ["fecha_hora", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_bookings_fecha_hora_deleted", table_name="bookings")
    op.drop_index("uq_bookings_slot_active", table_name="bookings")
