from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.review.entity import Review
from app.domain.review.ports import IReviewRepository, ReviewNotFound
from app.infrastructure.persistence.orm.review import ReviewORM


class SQLAlchemyReviewRepository(IReviewRepository):

    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def _to_entity(orm: ReviewORM) -> Review:
        # Creamos sin __post_init__ para no re-validar datos de la BD
        r = object.__new__(Review)
        r.id = orm.id
        r.nombre = orm.nombre
        r.valoracion = orm.valoracion
        r.comentario = orm.comentario
        r.visible = orm.visible
        r.created_at = orm.created_at
        return r

    def create(self, review: Review) -> Review:
        orm = ReviewORM(
            nombre=review.nombre,
            valoracion=review.valoracion,
            comentario=review.comentario,
            visible=review.visible,
        )
        self._session.add(orm)
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def get_by_id(self, review_id: int) -> Optional[Review]:
        orm = (
            self._session.query(ReviewORM)
            .filter(ReviewORM.id == review_id)
            .first()
        )
        return self._to_entity(orm) if orm else None

    def list(
        self,
        solo_visibles: bool = True,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Review]:
        query = self._session.query(ReviewORM)
        if solo_visibles:
            query = query.filter(ReviewORM.visible == True)  # noqa: E712
        query = query.order_by(ReviewORM.created_at.desc()).offset(skip)
        if limit is not None:
            query = query.limit(limit)
        return [self._to_entity(o) for o in query.all()]

    def count(self, solo_visibles: bool = True) -> int:
        query = self._session.query(func.count(ReviewORM.id))
        if solo_visibles:
            query = query.filter(ReviewORM.visible == True)  # noqa: E712
        return query.scalar() or 0

    def update(self, review: Review) -> Review:
        orm = (
            self._session.query(ReviewORM)
            .filter(ReviewORM.id == review.id)
            .first()
        )
        if not orm:
            raise ReviewNotFound(f"Reseña {review.id} no encontrada")
        orm.visible = review.visible
        orm.comentario = review.comentario
        self._session.commit()
        self._session.refresh(orm)
        return self._to_entity(orm)

    def delete(self, review_id: int) -> None:
        orm = (
            self._session.query(ReviewORM)
            .filter(ReviewORM.id == review_id)
            .first()
        )
        if not orm:
            raise ReviewNotFound(f"Reseña {review_id} no encontrada")
        self._session.delete(orm)
        self._session.commit()
