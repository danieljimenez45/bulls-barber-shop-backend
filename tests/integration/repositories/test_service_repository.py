"""Tests de integración del repositorio SQLAlchemy de Service."""

import pytest

from app.domain.service.entity import Service
from app.infrastructure.persistence.repositories.service import SQLAlchemyServiceRepository


def _service(nombre="Corte Clásico", activo=True, categoria="corte") -> Service:
    return Service(
        nombre=nombre,
        precio=15.0,
        descripcion="Corte de pelo clásico",
        duracion_minutos=30,
        categoria=categoria,
        activo=activo,
        orden=0,
    )


@pytest.mark.integration
def test_create_service(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    created = repo.create(_service())
    assert created.id is not None
    assert created.nombre == "Corte Clásico"


@pytest.mark.integration
def test_get_by_id(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    created = repo.create(_service())
    found = repo.get_by_id(created.id)
    assert found is not None
    assert found.id == created.id


@pytest.mark.integration
def test_list_solo_activos(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    repo.create(_service(nombre="Activo", activo=True))
    repo.create(_service(nombre="Inactivo", activo=False))
    activos = repo.list(solo_activos=True)
    assert all(s.activo for s in activos)
    assert len(activos) == 1


@pytest.mark.integration
def test_list_todos_incluyendo_inactivos(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    repo.create(_service(nombre="Activo", activo=True))
    repo.create(_service(nombre="Inactivo", activo=False))
    todos = repo.list(solo_activos=False)
    assert len(todos) == 2


@pytest.mark.integration
def test_update_service(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    created = repo.create(_service())
    created.nombre = "Corte Moderno"
    created.precio = 20.0
    updated = repo.update(created)
    assert updated.nombre == "Corte Moderno"
    assert updated.precio == 20.0


@pytest.mark.integration
def test_delete_service(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    created = repo.create(_service())
    repo.delete(created.id)
    assert repo.get_by_id(created.id) is None


@pytest.mark.integration
def test_count_activos(db_session):
    # El repo no tiene count(); usamos len(list(...)) como proxy
    repo = SQLAlchemyServiceRepository(db_session)
    repo.create(_service(nombre="A", activo=True))
    repo.create(_service(nombre="B", activo=True))
    repo.create(_service(nombre="C", activo=False))
    assert len(repo.list(solo_activos=True)) == 2
    assert len(repo.list(solo_activos=False)) == 3


@pytest.mark.integration
def test_update_inexistente_lanza_service_not_found(db_session):
    from app.domain.service.entity import Service
    from app.domain.service.ports import ServiceNotFound

    repo = SQLAlchemyServiceRepository(db_session)
    ghost = Service(
        id=9999,
        nombre="X",
        precio=10.0,
        duracion_minutos=30,
        categoria="corte",
    )
    with pytest.raises(ServiceNotFound):
        repo.update(ghost)


@pytest.mark.integration
def test_delete_inexistente_lanza_service_not_found(db_session):
    from app.domain.service.ports import ServiceNotFound

    repo = SQLAlchemyServiceRepository(db_session)
    with pytest.raises(ServiceNotFound):
        repo.delete(9999)


@pytest.mark.integration
def test_list_por_categoria(db_session):
    repo = SQLAlchemyServiceRepository(db_session)
    repo.create(_service(nombre="Corte", categoria="corte"))
    repo.create(_service(nombre="Barba", categoria="barba"))
    repo.create(_service(nombre="Pack", categoria="pack"))
    cortes = repo.list(solo_activos=True, categoria="corte")
    assert len(cortes) == 1
    assert cortes[0].categoria == "corte"
