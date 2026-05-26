"""Tests unitarios de casos de uso de servicios."""

import pytest

from app.domain.service.entity import Service
from app.domain.service.ports import ServiceNotFound
from app.domain.service.use_cases import UpdateServiceUseCase


@pytest.mark.unit
def test_update_service_asigna_campos_explicitos(mocker):
    repo = mocker.Mock()
    original = Service(
        id=1,
        nombre="Antiguo",
        descripcion="Desc",
        precio=10.0,
        duracion_minutos=30,
        categoria="corte",
        activo=True,
        orden=0,
    )
    repo.get_by_id.return_value = original
    repo.update.side_effect = lambda s: s

    UpdateServiceUseCase(repo).execute(1, nombre="Nuevo", precio=20.0)

    assert original.nombre == "Nuevo"
    assert original.precio == 20.0
    repo.update.assert_called_once()


@pytest.mark.unit
def test_update_service_no_encontrado(mocker):
    repo = mocker.Mock()
    repo.get_by_id.return_value = None

    with pytest.raises(ServiceNotFound):
        UpdateServiceUseCase(repo).execute(99, nombre="X")
