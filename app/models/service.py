from sqlalchemy import Boolean, Column, Float, Integer, String, Text

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text, nullable=True)
    precio = Column(Float, nullable=False)
    duracion_minutos = Column(Integer, default=30)
    # Ejemplos: "corte", "barba", "combo", "tratamiento"
    categoria = Column(String(50), default="corte")
    imagen_url = Column(String(255), nullable=True)
    activo = Column(Boolean, default=True)
    orden = Column(Integer, default=0)  # para ordenar en la web
