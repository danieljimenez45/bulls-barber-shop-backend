"""
conftest.py — Fixtures compartidas para toda la batería de tests.

Estrategia de aislamiento:
  - db_session: SQLite en memoria, creada y destruida por cada test.
  - client:     TestClient con app.dependency_overrides para inyectar la BD de test.
  - admin_token / auth_headers: JWT válido para llamadas a endpoints protegidos.

El startup de FastAPI llama a run_migrations() (Alembic). En tests lo reemplazamos
por un no-op y usamos Base.metadata.create_all() directamente sobre el engine
en memoria, evitando así la dependencia del fichero alembic.ini.
"""

import pytest
from fastapi.testclient import TestClient
from passlib.context import CryptContext
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

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest.fixture()
def db_session():
    """
    Sesión SQLite en memoria.
    Cada test arranca con un esquema limpio y sin datos previos.
    """
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


@pytest.fixture()
def client(db_session, monkeypatch):
    """
    TestClient de FastAPI con la BD de test inyectada.

    Parches aplicados:
    - run_migrations → no-op (evita la dependencia de alembic.ini en tests).
    - settings.RATE_LIMIT_ENABLED → False (el store de rate-limit es global y
      acumularía peticiones entre tests, provocando 429 falsos).
    """
    # Deshabilitar Alembic en el evento startup (main importa run_migrations por nombre)
    monkeypatch.setattr(db_module, "run_migrations", lambda: None)
    monkeypatch.setattr("app.main.run_migrations", lambda: None)

    # Deshabilitar rate limiting para no acumular contadores entre tests
    from app.config import settings as _settings
    monkeypatch.setattr(_settings, "RATE_LIMIT_ENABLED", False)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_user(db_session):
    """Crea un usuario admin en la BD de test y lo devuelve."""
    user_orm = UserORM(
        email="admin@test.com",
        hashed_password=_pwd.hash("test_password_123"),
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
