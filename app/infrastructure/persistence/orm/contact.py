from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ContactMessageORM(Base):
    """
    Modelo ORM para los mensajes recibidos a través del formulario de contacto.
    B-24: los mensajes se persisten en BD además de enviarse por email.
    """

    __tablename__ = "contact_messages"

    id        = Column(Integer,     primary_key=True, index=True)
    nombre    = Column(String(100), nullable=False)
    email     = Column(String(150), nullable=False)
    telefono  = Column(String(20),  nullable=True)
    asunto    = Column(String(200), nullable=True)
    mensaje   = Column(Text,        nullable=False)
    leido     = Column(Boolean,     default=False, nullable=False)
    created_at = Column(DateTime,   server_default=func.now())
