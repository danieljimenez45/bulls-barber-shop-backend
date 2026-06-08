from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class BookingORM(Base):
    __tablename__ = "bookings"

    id              = Column(Integer,      primary_key=True, index=True)
    nombre_cliente  = Column(String(100),  nullable=False)
    telefono        = Column(String(20),   nullable=False)
    email           = Column(String(100),  nullable=True)
    # FK → services.id con ON DELETE RESTRICT: no permite borrar un servicio
    # que tenga reservas vinculadas.  El PRAGMA foreign_keys=ON (database.py)
    # activa la comprobación en SQLite; PostgreSQL la aplica de forma nativa.
    servicio_id     = Column(Integer, ForeignKey("services.id", ondelete="RESTRICT"), nullable=False)
    servicio_nombre = Column(String(100),  nullable=True)
    fecha_hora      = Column(DateTime,     nullable=False)
    barbero         = Column(String(100),  nullable=True, default="Cualquier barbero")
    notas           = Column(Text,         nullable=True)
    estado          = Column(String(20),   default="pendiente")
    created_at      = Column(DateTime,     server_default=func.now())

    # B-22: soft-delete — NULL = activa, timestamp = eliminada por el admin
    # nullable=True para compatibilidad con registros previos sin migración Alembic
    deleted_at      = Column(DateTime,     nullable=True, default=None)
