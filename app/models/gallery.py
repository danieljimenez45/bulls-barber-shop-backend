from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class GalleryImage(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=True)
    descripcion = Column(Text, nullable=True)
    imagen_url = Column(String(255), nullable=False)
    # Ejemplos: "corte", "barba", "local", "equipo"
    categoria = Column(String(50), default="corte")
    visible = Column(Boolean, default=True)
    orden = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
