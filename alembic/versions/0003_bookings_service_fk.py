"""Añade FK bookings.servicio_id → services.id con ON DELETE RESTRICT.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-08 00:00:00.000000

Propósito:
  Impide borrar un servicio que tenga reservas vinculadas, protegiendo la
  integridad referencial en la capa de base de datos.

  La aplicación captura el IntegrityError resultante y devuelve HTTP 409 con
  el mensaje "Hay reservas vinculadas — desactiva el servicio en lugar de
  eliminarlo."

Notas de despliegue:
  SQLite   — render_as_batch=True en env.py hace que Alembic recree la tabla
             en lote; funciona sin necesidad de soporte nativo de ALTER TABLE.
  PostgreSQL — ALTER TABLE ... ADD CONSTRAINT fk_... nativo; no hay impacto.

Para bases de datos existentes (ya en producción con la migración 0001):
    alembic upgrade 0003
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# ── Identificadores de revisión ────────────────────────────────────────────────
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Añade la FK bookings.servicio_id → services.id ON DELETE RESTRICT."""
    # batch_alter_table es necesario para SQLite (que no soporta ADD CONSTRAINT
    # nativo).  render_as_batch=True en env.py selecciona automáticamente el
    # modo correcto según el dialecto.
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_bookings_servicio_id_services",
            "services",
            ["servicio_id"],
            ["id"],
            ondelete="RESTRICT",
        )


def downgrade() -> None:
    """Elimina la FK añadida en upgrade()."""
    with op.batch_alter_table("bookings", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_bookings_servicio_id_services",
            type_="foreignkey",
        )
