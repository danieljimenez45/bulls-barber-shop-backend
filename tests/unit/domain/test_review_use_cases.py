"""Tests unitarios de los casos de uso de reseñas."""

import pytest

from app.domain.review.entity import Review
from app.domain.review.ports import ReviewNotFound
from app.domain.review.use_cases import (
    CreateReviewUseCase,
    DeleteReviewUseCase,
    ListReviewsUseCase,
    ToggleVisibilityUseCase,
)


def _review(id_=1, visible=True) -> Review:
    r = Review(nombre="Ana", valoracion=5)
    r.id = id_
    r.visible = visible
    return r


# ── CreateReviewUseCase ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_crear_resena_delega_en_repo(mocker):
    repo = mocker.Mock()
    repo.create.return_value = _review()
    uc = CreateReviewUseCase(repo)
    result = uc.execute(Review(nombre="Ana", valoracion=5))
    assert result.id == 1
    repo.create.assert_called_once()


# ── ListReviewsUseCase ─────────────────────────────────────────────────────────

@pytest.mark.unit
def test_listar_resenas_devuelve_items_y_total(mocker):
    repo = mocker.Mock()
    repo.list.return_value = [_review(1), _review(2)]
    repo.count.return_value = 2
    uc = ListReviewsUseCase(repo)
    items, total = uc.execute(solo_visibles=True)
    assert len(items) == 2
    assert total == 2


@pytest.mark.unit
def test_listar_resenas_pasa_skip_y_limit(mocker):
    repo = mocker.Mock()
    repo.list.return_value = []
    repo.count.return_value = 0
    uc = ListReviewsUseCase(repo)
    uc.execute(solo_visibles=True, skip=20, limit=10)
    repo.list.assert_called_once_with(solo_visibles=True, skip=20, limit=10)


# ── ToggleVisibilityUseCase ────────────────────────────────────────────────────

@pytest.mark.unit
def test_ocultar_resena(mocker):
    r = _review(visible=True)
    repo = mocker.Mock()
    repo.get_by_id.return_value = r
    repo.update.return_value = r
    uc = ToggleVisibilityUseCase(repo)
    uc.execute(1, visible=False)
    assert r.visible is False


@pytest.mark.unit
def test_mostrar_resena(mocker):
    r = _review(visible=False)
    repo = mocker.Mock()
    repo.get_by_id.return_value = r
    repo.update.return_value = r
    uc = ToggleVisibilityUseCase(repo)
    uc.execute(1, visible=True)
    assert r.visible is True


@pytest.mark.unit
def test_toggle_visibilidad_not_found_lanza_error(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None
    uc = ToggleVisibilityUseCase(repo)
    with pytest.raises(ReviewNotFound):
        uc.execute(999, visible=True)


# ── DeleteReviewUseCase ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_eliminar_resena_llama_repo_delete(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = _review()
    uc = DeleteReviewUseCase(repo)
    uc.execute(1)
    repo.delete.assert_called_once_with(1)


@pytest.mark.unit
def test_eliminar_resena_not_found_lanza_error(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None
    uc = DeleteReviewUseCase(repo)
    with pytest.raises(ReviewNotFound):
        uc.execute(999)
