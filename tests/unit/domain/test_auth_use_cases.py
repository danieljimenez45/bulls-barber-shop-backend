"""Tests unitarios de los casos de uso de autenticación."""

import pytest

from app.domain.auth.entity import AdminUser
from app.domain.auth.ports import InvalidCredentials, TokenInvalid
from app.domain.auth.use_cases import GetCurrentAdminUseCase, LoginUseCase


# ── Helpers ────────────────────────────────────────────────────────────────────

def _admin(id_: int = 1, is_active: bool = True) -> AdminUser:
    return AdminUser(
        id=id_,
        email="admin@test.com",
        hashed_password="hashed_pass",
        is_active=is_active,
    )


# ── LoginUseCase ───────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_login_correcto_devuelve_token(mocker):
    """Login con credenciales válidas debe devolver un token no vacío."""
    repo = mocker.Mock()
    repo.find_by_email.return_value = _admin()

    hasher = mocker.Mock()
    hasher.verify.return_value = True

    token_svc = mocker.Mock()
    token_svc.create_token.return_value = "jwt.token.fake"

    uc = LoginUseCase(repo, hasher, token_svc)
    token = uc.execute("admin@test.com", "password123")

    assert token == "jwt.token.fake"
    token_svc.create_token.assert_called_once()


@pytest.mark.unit
def test_login_password_incorrecta_lanza_invalid_credentials(mocker):
    """Contraseña incorrecta debe lanzar InvalidCredentials."""
    repo = mocker.Mock()
    repo.find_by_email.return_value = _admin()

    hasher = mocker.Mock()
    hasher.verify.return_value = False

    token_svc = mocker.Mock()

    uc = LoginUseCase(repo, hasher, token_svc)
    with pytest.raises(InvalidCredentials):
        uc.execute("admin@test.com", "wrong_password")

    token_svc.create_token.assert_not_called()


@pytest.mark.unit
def test_login_usuario_no_encontrado_lanza_invalid_credentials(mocker):
    """Email inexistente debe lanzar InvalidCredentials sin revelar cuál falló."""
    repo = mocker.Mock()
    repo.find_by_email.return_value = None

    hasher = mocker.Mock()
    token_svc = mocker.Mock()

    uc = LoginUseCase(repo, hasher, token_svc)
    with pytest.raises(InvalidCredentials):
        uc.execute("noexiste@test.com", "any_password")

    hasher.verify.assert_not_called()
    token_svc.create_token.assert_not_called()


@pytest.mark.unit
def test_login_usuario_inactivo_lanza_invalid_credentials(mocker):
    """Usuario con is_active=False debe lanzar InvalidCredentials."""
    repo = mocker.Mock()
    repo.find_by_email.return_value = _admin(is_active=False)

    hasher = mocker.Mock()
    token_svc = mocker.Mock()

    uc = LoginUseCase(repo, hasher, token_svc)
    with pytest.raises(InvalidCredentials):
        uc.execute("admin@test.com", "password123")

    hasher.verify.assert_not_called()


# ── GetCurrentAdminUseCase ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_get_current_admin_token_valido_devuelve_usuario(mocker):
    """Token válido debe devolver el AdminUser correspondiente."""
    repo = mocker.Mock()
    repo.find_by_id.return_value = _admin(id_=3)

    token_svc = mocker.Mock()
    token_svc.decode_token.return_value = {"sub": "3"}

    uc = GetCurrentAdminUseCase(repo, token_svc)
    user = uc.execute("valid.jwt.token")

    assert user.id == 3
    repo.find_by_id.assert_called_once_with(3)


@pytest.mark.unit
def test_get_current_admin_token_invalido_lanza_token_invalid(mocker):
    """Un token inválido (decode falla) debe propagar TokenInvalid."""
    repo = mocker.Mock()

    token_svc = mocker.Mock()
    token_svc.decode_token.side_effect = TokenInvalid("Token inválido")

    uc = GetCurrentAdminUseCase(repo, token_svc)
    with pytest.raises(TokenInvalid):
        uc.execute("invalid.token")

    repo.find_by_id.assert_not_called()


@pytest.mark.unit
def test_get_current_admin_usuario_no_encontrado_lanza_token_invalid(mocker):
    """Si el ID del token no corresponde a ningún usuario debe lanzar TokenInvalid."""
    repo = mocker.Mock()
    repo.find_by_id.return_value = None

    token_svc = mocker.Mock()
    token_svc.decode_token.return_value = {"sub": "999"}

    uc = GetCurrentAdminUseCase(repo, token_svc)
    with pytest.raises(TokenInvalid):
        uc.execute("token.with.missing.user")


@pytest.mark.unit
def test_get_current_admin_token_sin_subject_lanza_token_invalid(mocker):
    """Token decodificado sin campo 'sub' debe lanzar TokenInvalid."""
    repo = mocker.Mock()

    token_svc = mocker.Mock()
    token_svc.decode_token.return_value = {}  # sin sub

    uc = GetCurrentAdminUseCase(repo, token_svc)
    with pytest.raises(TokenInvalid):
        uc.execute("token.without.sub")

    repo.find_by_id.assert_not_called()
