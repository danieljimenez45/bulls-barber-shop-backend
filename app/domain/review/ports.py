from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.review.entity import Review


class ReviewNotFound(Exception):
    """Se lanza cuando no se encuentra una reseña por su ID."""


class IReviewRepository(ABC):

    @abstractmethod
    def create(self, review: Review) -> Review: ...

    @abstractmethod
    def get_by_id(self, review_id: int) -> Optional[Review]: ...

    @abstractmethod
    def list(
        self,
        solo_visibles: bool = True,
        skip: int = 0,
        limit: Optional[int] = None,
    ) -> List[Review]: ...

    @abstractmethod
    def count(self, solo_visibles: bool = True) -> int: ...

    @abstractmethod
    def update(self, review: Review) -> Review: ...

    @abstractmethod
    def delete(self, review_id: int) -> None: ...
