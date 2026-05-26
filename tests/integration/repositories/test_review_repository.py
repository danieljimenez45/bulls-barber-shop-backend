"""Tests de integración del repositorio de reseñas."""

import pytest

from app.domain.review.entity import Review
from app.domain.review.ports import ReviewNotFound
from app.infrastructure.persistence.repositories.review import SQLAlchemyReviewRepository


def _review(**kwargs) -> Review:
    defaults = dict(nombre="Cliente", valoracion=5, comentario="Genial")
    defaults.update(kwargs)
    return Review(**defaults)


@pytest.mark.integration
def test_create_y_get_by_id(db_session):
    repo = SQLAlchemyReviewRepository(db_session)
    created = repo.create(_review())
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.valoracion == 5


@pytest.mark.integration
def test_list_solo_visibles(db_session):
    repo = SQLAlchemyReviewRepository(db_session)
    repo.create(_review(nombre="Visible"))
    r2 = repo.create(_review(nombre="Oculta"))
    r2.visible = False
    repo.update(r2)

    visibles = repo.list(solo_visibles=True)
    assert len(visibles) == 1
    assert repo.count(solo_visibles=True) == 1


@pytest.mark.integration
def test_update_visibilidad(db_session):
    repo = SQLAlchemyReviewRepository(db_session)
    created = repo.create(_review())
    created.ocultar()
    updated = repo.update(created)
    assert updated.visible is False


@pytest.mark.integration
def test_delete_resena(db_session):
    repo = SQLAlchemyReviewRepository(db_session)
    created = repo.create(_review())
    repo.delete(created.id)
    assert repo.get_by_id(created.id) is None


@pytest.mark.integration
def test_update_inexistente_lanza_review_not_found(db_session):
    repo = SQLAlchemyReviewRepository(db_session)
    ghost = _review()
    ghost.id = 9999
    with pytest.raises(ReviewNotFound):
        repo.update(ghost)
