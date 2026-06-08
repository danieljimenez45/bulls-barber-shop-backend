"""Añade columna duracion_minutos a la tabla bookings.

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-08 00:00:00.000000

Propósito:
  Almacena la duración del servicio en el momento de la reserva.
  Necesario para la lógica de solapamiento del grid :00/:30:
  una reserva de 60 min a las 10:00 bloquea también el slot de las 10:30.

  El valor por defecto 30 aplica a todos los registros existentes.
"""

from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "duracion_minutos",
                sa.Integer(),
                nullable=False,
                server_default="30",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_column("duracion_minutos")
