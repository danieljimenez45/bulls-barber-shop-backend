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
def test_send_contact_notifier_falla_propaga_excepcion(mocker):
    repo = mocker.Mock()
    notifier = mocker.Mock()
    notifier.notify.side_effect = RuntimeError("SMTP caído")
    repo.save.return_value = _msg(id_=2)

    uc = SendContactMessageUseCase(notifier=notifier, repository=repo)
    with pytest.raises(RuntimeError, match="SMTP"):
        uc.execute(_msg())


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
