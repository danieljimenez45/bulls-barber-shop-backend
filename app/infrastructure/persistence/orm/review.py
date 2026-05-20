from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ReviewORM(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    valoracion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=True)
    visible = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
