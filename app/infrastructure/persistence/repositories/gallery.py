from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.gallery.entity import GalleryImage
from app.domain.gallery.ports import IGalleryRepository, ImageNotFound
from app.infrastructure.persistence.orm.gallery import GalleryORM


class SQLAlchemyGalleryRepository(IGalleryRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_entity(orm: GalleryORM) -> GalleryImage:
        return GalleryImage(
            id=orm.id,
            titulo=orm.titulo,
            descripcion=orm.descripcion,
            imagen_url=orm.imagen_url,
            categoria=orm.categoria,
            visible=orm.visible,
            orden=orm.orden,
            created_at=orm.created_at,
        )

    def add(self, image: GalleryImage) -> GalleryImage:
        orm = GalleryORM(
            titulo=image.titulo,
            descripcion=image.descripcion,
            imagen_url=image.imagen_url,
            categoria=image.categoria,
            visible=image.visible,
            orden=image.orden,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def get_by_id(self, image_id: int) -> Optional[GalleryImage]:
        orm = (
            self._session.query(GalleryORM)
            .filter(GalleryORM.id == image_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def list(
        self,
        categoria: Optional[str] = None,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[GalleryImage]:
        query = self._session.query(GalleryORM).filter(
            GalleryORM.visible == True  # noqa: E712
        )
        if categoria:
            query = query.filter(GalleryORM.categoria == categoria)
        query = query.order_by(GalleryORM.orden, GalleryORM.created_at.desc()).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return [self._to_entity(o) for o in query.all()]

    def count(self, categoria: Optional[str] = None) -> int:
        query = self._session.query(func.count(GalleryORM.id)).filter(
            GalleryORM.visible == True  # noqa: E712
        )
        if categoria:
            query = query.filter(GalleryORM.categoria == categoria)
        return query.scalar() or 0

    def delete(self, image_id: int) -> None:
        orm = (
            self._session.query(GalleryORM)
            .filter(GalleryORM.id == image_id)
            .first()
        )
        if not orm:
            raise ImageNotFound(f"Imagen {image_id} no encontrada")
        self._session.delete(orm)
        self._session.commit()
