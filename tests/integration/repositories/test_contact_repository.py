"""Tests de integración del repositorio de mensajes de contacto."""

import pytest

from app.domain.contact.entity import ContactMessage
from app.domain.contact.ports import ContactMessageNotFound
from app.infrastructure.persistence.repositories.contact import SQLAlchemyContactRepository


def _message(**kwargs) -> ContactMessage:
    defaults = dict(
        nombre="Ana",
        email="ana@test.com",
        telefono="600111222",
        asunto="Consulta",
        mensaje="Hola, quisiera información.",
    )
    defaults.update(kwargs)
    return ContactMessage(**defaults)


@pytest.mark.integration
def test_save_y_get_by_id(db_session):
    repo = SQLAlchemyContactRepository(db_session)
    saved = repo.save(_message())
    found = repo.get_by_id(saved.id)
    assert found is not None
    assert found.email == "ana@test.com"


@pytest.mark.integration
def test_list_con_filtro_solo_no_leidos(db_session):
    repo = SQLAlchemyContactRepository(db_session)
    repo.save(_message())
    m2 = repo.save(_message(email="b@test.com"))
    repo.mark_as_read(m2.id)

    items, total = repo.list(solo_no_leidos=True)
    assert total == 1
    assert len(items) == 1


@pytest.mark.integration
def test_mark_as_read(db_session):
    repo = SQLAlchemyContactRepository(db_session)
    saved = repo.save(_message())
    updated = repo.mark_as_read(saved.id)
    assert updated.leido is True


@pytest.mark.integration
def test_mark_as_read_inexistente_lanza_error(db_session):
    repo = SQLAlchemyContactRepository(db_session)
    with pytest.raises(ContactMessageNotFound):
        repo.mark_as_read(9999)
