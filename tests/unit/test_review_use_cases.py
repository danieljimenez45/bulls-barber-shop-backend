"""Tests unitarios de los casos de uso de reseñas."""

from unittest.mock import MagicMock

import pytest

from app.domain.review.entity import Review
from app.domain.review.ports import ReviewNotFound
from app.domain.review.use_cases import (
    CreateReviewUseCase,
    DeleteReviewUseCase,
    ListReviewsUseCase,
    ToggleVisibilityUseCase,
)


def _review(id=1, visible=True) -> Review:
    r = Review(nombre="Ana", valoracion=5)
    r.id = id
    r.visible = visible
    return r


class TestCreateReviewUseCase:
    def test_crea_resena(self):
        repo = MagicMock()
        repo.create.return_value = _review()
        uc = CreateReviewUseCase(repo)
        result = uc.execute(Review(nombre="Ana", valoracion=5))
        assert result.id == 1
        repo.create.assert_called_once()


class TestListReviewsUseCase:
    def test_devuelve_items_y_total(self):
        repo = MagicMock()
        repo.list.return_value = [_review(1), _review(2)]
        repo.count.return_value = 2
        uc = ListReviewsUseCase(repo)
        items, total = uc.execute(solo_visibles=True)
        assert len(items) == 2
        assert total == 2

    def test_pasa_skip_y_limit(self):
        repo = MagicMock()
        repo.list.return_value = []
        repo.count.return_value = 0
        uc = ListReviewsUseCase(repo)
        uc.execute(solo_visibles=True, skip=20, limit=10)
        repo.list.assert_called_once_with(solo_visibles=True, skip=20, limit=10)


class TestToggleVisibilityUseCase:
    def test_oculta_resena(self):
        r = _review(visible=True)
        repo = MagicMock()
        repo.get_by_id.return_value = r
        repo.update.return_value = r
        uc = ToggleVisibilityUseCase(repo)
        uc.execute(1, visible=False)
        assert r.visible is False

    def test_muestra_resena(self):
        r = _review(visible=False)
        repo = MagicMock()
        repo.get_by_id.return_value = r
        repo.update.return_value = r
        uc = ToggleVisibilityUseCase(repo)
        uc.execute(1, visible=True)
        assert r.visible is True

    def test_lanza_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        uc = ToggleVisibilityUseCase(repo)
        with pytest.raises(ReviewNotFound):
            uc.execute(999, visible=True)


class TestDeleteReviewUseCase:
    def test_elimina(self):
        repo = MagicMock()
        repo.get_by_id.return_value = _review()
        uc = DeleteReviewUseCase(repo)
        uc.execute(1)
        repo.delete.assert_called_once_with(1)

    def test_lanza_not_found(self):
        repo = MagicMock()
        repo.get_by_id.return_value = None
        uc = DeleteReviewUseCase(repo)
        with pytest.raises(ReviewNotFound):
            uc.execute(999)
