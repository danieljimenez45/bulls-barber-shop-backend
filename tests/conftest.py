"""
Fixtures compartidas para toda la suite de tests.

- `db_session`  → sesión SQLAlchemy sobre SQLite en memoria
- `client`      → TestClient de FastAPI con BD de test inyectada
- `admin_token` → JWT válido para rutas protegidas
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# ── Base de datos en memoria ───────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite:///:memory:"

_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
_TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _create_all():
    from app.infrastructure.persistence.orm import (  # noqa: F401
        booking, gallery, review, service, user,
    )
    Base.metadata.create_all(bind=_engine)


def _drop_all():
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture(scope="function")
def db_session():
    """Sesión de BD fresca por test (crea y destruye tablas)."""
    _create_all()
    session = _TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        _drop_all()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient con la BD de test inyectada. Rate limiting deshabilitado."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Deshabilitar rate limiting en tests
    import app.config as cfg
    original = cfg.settings.RATE_LIMIT_ENABLED
    cfg.settings.RATE_LIMIT_ENABLED = False

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c

    app.dependency_overrides.clear()
    cfg.settings.RATE_LIMIT_ENABLED = original


@pytest.fixture
def admin_token(client):
    """
    Crea un admin en la BD de test y devuelve un JWT válido.
    Depende de `client` para tener la sesión correcta inyectada.
    """
    from app.infrastructure.persistence.orm.user import UserORM
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher
    from app.infrastructure.security.jwt_service import JWTService

    # Crear usuario admin directamente en la BD de test
    hasher = BcryptPasswordHasher()
    hashed = hasher.hash("TestPass123!")

    # Acceder a la sesión de test a través del override
    db = next(app.dependency_overrides[get_db]())
    user = UserORM(email="test@admin.com", hashed_password=hashed, is_active=True)
    db.add(user)
    db.commit()

    jwt = JWTService()
    token = jwt.create_token({"sub": "test@admin.com"})
    return token
