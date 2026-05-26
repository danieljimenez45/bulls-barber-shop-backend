"""Tests de integración del repositorio de galería."""

import pytest

from app.domain.gallery.entity import GalleryImage
from app.domain.gallery.ports import ImageNotFound
from app.infrastructure.persistence.repositories.gallery import SQLAlchemyGalleryRepository


def _image(**kwargs) -> GalleryImage:
    defaults = dict(imagen_url="/uploads/test.png", categoria="corte", visible=True)
    defaults.update(kwargs)
    return GalleryImage(**defaults)


@pytest.mark.integration
def test_add_y_get_by_id(db_session):
    repo = SQLAlchemyGalleryRepository(db_session)
    created = repo.add(_image(titulo="Foto 1"))
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.titulo == "Foto 1"


@pytest.mark.integration
def test_list_solo_visibles_y_filtro_categoria(db_session):
    repo = SQLAlchemyGalleryRepository(db_session)
    repo.add(_image(categoria="corte"))
    repo.add(_image(categoria="barba", imagen_url="/b.png"))
    repo.add(_image(categoria="corte", visible=False, imagen_url="/oculta.png"))

    items = repo.list(categoria="corte")
    assert len(items) == 1
    assert repo.count(categoria="corte") == 1


@pytest.mark.integration
def test_delete_imagen(db_session):
    repo = SQLAlchemyGalleryRepository(db_session)
    created = repo.add(_image())
    repo.delete(created.id)
    assert repo.get_by_id(created.id) is None


@pytest.mark.integration
def test_delete_inexistente_lanza_image_not_found(db_session):
    repo = SQLAlchemyGalleryRepository(db_session)
    with pytest.raises(ImageNotFound):
        repo.delete(9999)
