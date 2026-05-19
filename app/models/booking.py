from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    nombre_cliente = Column(String(100), nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    servicio_id = Column(Integer, nullable=False)
    servicio_nombre = Column(String(100), nullable=True)  # copia legible
    fecha_hora = Column(DateTime, nullable=False)
    barbero = Column(String(100), nullable=True, default="Cualquier barbero")
    notas = Column(Text, nullable=True)
    # pendiente | confirmada | cancelada | completada
    estado = Column(String(20), default="pendiente")
    created_at = Column(DateTime, server_default=func.now())
