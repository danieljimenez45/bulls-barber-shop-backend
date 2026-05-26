"""Tests unitarios de casos de uso de galería."""

import pytest

from app.domain.gallery.entity import GalleryImage
from app.domain.gallery.ports import ImageNotFound
from app.domain.gallery.use_cases import DeleteImageUseCase, ListImagesUseCase, UploadImageUseCase


@pytest.mark.unit
def test_list_images_delega_en_repo(mocker):
    repo = mocker.Mock()
    repo.list.return_value = [GalleryImage(id=1, imagen_url="/a.png")]
    repo.count.return_value = 1

    items, total = ListImagesUseCase(repo).execute(categoria="corte", skip=0, limit=10)

    assert len(items) == 1
    assert total == 1
    repo.list.assert_called_once_with(categoria="corte", skip=0, limit=10)


@pytest.mark.unit
def test_upload_image_guarda_en_storage_y_repo(mocker):
    repo = mocker.Mock()
    storage = mocker.Mock()
    storage.save.return_value = "https://cdn/img.png"
    repo.add.return_value = GalleryImage(id=2, imagen_url="https://cdn/img.png")

    result = UploadImageUseCase(repo, storage).execute(b"data", "png", titulo="T")

    storage.save.assert_called_once_with(b"data", "png")
    repo.add.assert_called_once()
    assert result.imagen_url == "https://cdn/img.png"


@pytest.mark.unit
def test_delete_image_no_encontrada_lanza_error(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None

    with pytest.raises(ImageNotFound):
        DeleteImageUseCase(repo, mocker.Mock()).execute(99)


@pytest.mark.unit
def test_delete_image_repo_primero_luego_storage(mocker):
    repo = mocker.Mock()
    storage = mocker.Mock()
    repo.get_by_id.return_value = GalleryImage(id=3, imagen_url="https://cdn/x.png")
    order: list[str] = []

    def _repo_delete(image_id: int) -> None:
        order.append("repo")

    def _storage_delete(url: str) -> None:
        order.append("storage")

    repo.delete.side_effect = _repo_delete
    storage.delete.side_effect = _storage_delete

    DeleteImageUseCase(repo, storage).execute(3)

    assert order == ["repo", "storage"]
    repo.delete.assert_called_once_with(3)
    storage.delete.assert_called_once_with("https://cdn/x.png")
