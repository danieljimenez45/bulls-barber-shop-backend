"""Tests de integración del repositorio de usuarios admin."""

import pytest

from app.domain.auth.entity import AdminUser
from app.infrastructure.persistence.repositories.user import SQLAlchemyUserRepository
from app.infrastructure.security.password_hasher import BcryptPasswordHasher


@pytest.mark.integration
def test_find_by_email_y_find_by_id(db_session):
    hasher = BcryptPasswordHasher()
    repo = SQLAlchemyUserRepository(db_session)
    created = repo.create(
        AdminUser(
            email="admin@repo.test",
            hashed_password=hasher.hash("secret123"),
            is_active=True,
        )
    )

    by_email = repo.find_by_email("admin@repo.test")
    by_id = repo.find_by_id(created.id)

    assert by_email is not None
    assert by_id is not None
    assert by_email.email == "admin@repo.test"


@pytest.mark.integration
def test_find_by_email_inexistente_devuelve_none(db_session):
    repo = SQLAlchemyUserRepository(db_session)
    assert repo.find_by_email("noexiste@test.com") is None
