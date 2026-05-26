"""Tests unitarios de LocalFileStorage."""

import pytest

from app.infrastructure.storage.local import LocalFileStorage


@pytest.mark.unit
def test_delete_path_traversal_lanza_value_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    storage = LocalFileStorage(upload_dir="uploads/gallery")

    with pytest.raises(ValueError, match="no permitida"):
        storage.delete("/uploads/gallery/../../../etc/passwd")
