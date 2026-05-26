"""
conftest.py — Fixtures compartidas para toda la batería de tests.

Estrategia de aislamiento:
  - db_session: SQLite en memoria, esquema limpio por test.
  - client (session): un TestClient / lifespan por worker (no repetir startup).
  - admin_user: hash bcrypt precalculado (rounds=4 en tests).

Velocidad: pytest -n auto  (pytest-xdist, un proceso por núcleo)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database as db_module
from app.database import Base, get_db
from app.infrastructure.persistence.orm import (  # noqa: F401 — registra tablas
    booking,
    contact,
    gallery,
    review,
    service,
    user,
)
from app.infrastructure.persistence.orm.user import UserORM
from app.infrastructure.security.jwt_service import JWTService
from app.main import app

# bcrypt rounds=4, password "test_password_123" — ~50 ms menos por test con admin_user
_ADMIN_PASSWORD_HASH = (
    "$2b$04$.VyCHpUfveoqhpVoKeKYAeRXNHIsoqI07JLH.m6OHumqm5DgyWBdK"
)


@pytest.fixture()
def db_session():
    """Sesión SQLite en memoria. Cada test arranca con esquema y datos limpios."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="session")
def _test_client():
    """Un TestClient por worker: evita ejecutar lifespan en cada test (~0,2 s c/u)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture()
def client(_test_client, db_session, monkeypatch):
    """
    TestClient con la BD de test inyectada.

    Parches por test:
    - run_migrations → no-op
    - RATE_LIMIT_ENABLED → False (salvo tests que lo reactivan)
    """
    monkeypatch.setattr(db_module, "run_migrations", lambda: None)
    monkeypatch.setattr("app.main.run_migrations", lambda: None)

    from app.config import settings as _settings

    monkeypatch.setattr(_settings, "RATE_LIMIT_ENABLED", False)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    yield _test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_booking_service(db_session):
    """Servicio activo id=1 para tests de reservas (validación en router)."""
    from app.infrastructure.persistence.orm.service import ServiceORM

    if db_session.query(ServiceORM).filter_by(id=1).first() is not None:
        return
    svc = ServiceORM(
        nombre="Corte Clásico",
        descripcion="Corte tradicional",
        precio=15.0,
        duracion_minutos=30,
        categoria="corte",
        activo=True,
        orden=0,
    )
    db_session.add(svc)
    db_session.commit()


@pytest.fixture()
def admin_user(db_session):
    """Crea un usuario admin en la BD de test y lo devuelve."""
    user_orm = UserORM(
        email="admin@test.com",
        hashed_password=_ADMIN_PASSWORD_HASH,
        is_active=True,
    )
    db_session.add(user_orm)
    db_session.commit()
    db_session.refresh(user_orm)
    return user_orm


@pytest.fixture()
def admin_token(admin_user):
    """Genera un JWT válido para el usuario admin de test."""
    jwt_service = JWTService()
    return jwt_service.create_token({"sub": str(admin_user.id)})


@pytest.fixture()
def auth_headers(admin_token):
    """Cabeceras HTTP con el JWT del admin, listas para pasar a client."""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def mock_booking_notifier(mocker):
    """Evita envíos SMTP reales en tests que crean reservas."""
    return mocker.patch(
        "app.api.routers.bookings.SMTPBookingNotifier",
        return_value=mocker.Mock(),
    )
