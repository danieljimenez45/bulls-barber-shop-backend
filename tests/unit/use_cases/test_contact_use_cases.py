"""Tests unitarios de los casos de uso de ContactMessage."""

import pytest

from app.domain.contact.entity import ContactMessage
from app.domain.contact.use_cases import (
    ListContactMessagesUseCase,
    MarkMessageReadUseCase,
    SendContactMessageUseCase,
)


def _msg(id_=None, leido=False) -> ContactMessage:
    return ContactMessage(
        id=id_,
        nombre="Ana López",
        email="ana@example.com",
        mensaje="Hola, quiero información.",
        leido=leido,
    )


# ── SendContactMessageUseCase ──────────────────────────────────────────────────

@pytest.mark.unit
def test_send_contact_guarda_en_repo_si_existe(mocker):
    repo = mocker.Mock()
    notifier = mocker.Mock()
    saved = _msg(id_=1)
    repo.save.return_value = saved

    uc = SendContactMessageUseCase(notifier=notifier, repository=repo)
    result = uc.execute(_msg())

    repo.save.assert_called_once()
    notifier.notify.assert_called_once_with(saved)
    assert result.id == 1


@pytest.mark.unit
def test_send_contact_notifica_aunque_falle_el_repo(mocker):
    """Si el notifier falla, el use case no re-lanza la excepción."""
    repo = mocker.Mock()
    notifier = mocker.Mock()
    notifier.notify.side_effect = RuntimeError("SMTP caído")
    repo.save.return_value = _msg(id_=2)

    uc = SendContactMessageUseCase(notifier=notifier, repository=repo)
    result = uc.execute(_msg())  # no debe explotar

    assert result.id == 2


@pytest.mark.unit
def test_send_contact_sin_repo_solo_notifica(mocker):
    notifier = mocker.Mock()

    uc = SendContactMessageUseCase(notifier=notifier, repository=None)
    msg = _msg()
    result = uc.execute(msg)

    notifier.notify.assert_called_once_with(msg)
    assert result.id is None  # sin repo no hay id


# ── ListContactMessagesUseCase ─────────────────────────────────────────────────

@pytest.mark.unit
def test_list_messages_delega_al_repo(mocker):
    repo = mocker.Mock()
    repo.list.return_value = ([_msg(id_=1), _msg(id_=2)], 2)

    uc = ListContactMessagesUseCase(repo)
    items, total = uc.execute()

    repo.list.assert_called_once()
    assert total == 2
    assert len(items) == 2


# ── MarkMessageReadUseCase ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_mark_read_delega_al_repo(mocker):
    repo = mocker.Mock()
    repo.mark_as_read.return_value = _msg(id_=1, leido=True)

    uc = MarkMessageReadUseCase(repo)
    result = uc.execute(1)

    repo.mark_as_read.assert_called_once_with(1)
    assert result.leido is True


@pytest.mark.unit
def test_mark_read_no_encontrado_lanza_excepcion(mocker):
    from app.domain.contact.ports import ContactMessageNotFound

    repo = mocker.Mock()
    repo.mark_as_read.side_effect = ContactMessageNotFound("No existe")

    uc = MarkMessageReadUseCase(repo)
    with pytest.raises(ContactMessageNotFound):
        uc.execute(99)
