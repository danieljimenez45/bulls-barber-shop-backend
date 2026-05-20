from typing import List

from app.domain.review.entity import Review
from app.domain.review.ports import IReviewRepository, ReviewNotFound


class CreateReviewUseCase:
    def __init__(self, repo: IReviewRepository) -> None:
        self._repo = repo

    def execute(self, review: Review) -> Review:
        return self._repo.create(review)


class ListReviewsUseCase:
    def __init__(self, repo: IReviewRepository) -> None:
        self._repo = repo

    def execute(self, solo_visibles: bool = True) -> List[Review]:
        return self._repo.list(solo_visibles=solo_visibles)


class ToggleVisibilityUseCase:
    def __init__(self, repo: IReviewRepository) -> None:
        self._repo = repo

    def execute(self, review_id: int, visible: bool) -> Review:
        review = self._repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Reseña {review_id} no encontrada")
        if visible:
            review.mostrar()
        else:
            review.ocultar()
        return self._repo.update(review)


class DeleteReviewUseCase:
    def __init__(self, repo: IReviewRepository) -> None:
        self._repo = repo

    def execute(self, review_id: int) -> None:
        review = self._repo.get_by_id(review_id)
        if not review:
            raise ReviewNotFound(f"Reseña {review_id} no encontrada")
        self._repo.delete(review_id)
