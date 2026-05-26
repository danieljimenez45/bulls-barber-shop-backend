"""Tests de utilidades de base de datos (sin BD real)."""

import pytest


@pytest.mark.unit
def test_run_migrations_invoca_alembic_upgrade(mocker):
    mock_upgrade = mocker.patch("alembic.command.upgrade")
    mocker.patch("alembic.config.Config")

    from app.database import run_migrations

    run_migrations()
    mock_upgrade.assert_called_once()
    assert mock_upgrade.call_args[0][1] == "head"


@pytest.mark.unit
def test_create_tables_crea_metadata(mocker):
    mock_create_all = mocker.patch("app.database.Base.metadata.create_all")

    from app.database import create_tables

    create_tables()
    mock_create_all.assert_called_once()
