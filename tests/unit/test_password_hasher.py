"""Tests del hasher bcrypt."""

import pytest

from app.infrastructure.security.password_hasher import BcryptPasswordHasher


@pytest.mark.unit
def test_hash_y_verify_coinciden():
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("mi_password_seguro")
    assert hasher.verify("mi_password_seguro", hashed)


@pytest.mark.unit
def test_verify_password_incorrecta_devuelve_false():
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("correcta")
    assert hasher.verify("incorrecta", hashed) is False
