"""Tests de integración para el endpoint /api/auth."""

from app.infrastructure.persistence.orm.user import UserORM
from app.infrastructure.security.password_hasher import BcryptPasswordHasher


def _create_admin(db_session, email="admin@test.com", password="AdminPass123!"):
    hasher = BcryptPasswordHasher()
    user = UserORM(
        email=email,
        hashed_password=hasher.hash(password),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return email, password


class TestLogin:
    def test_login_correcto_devuelve_token(self, client, db_session):
        email, password = _create_admin(db_session)
        resp = client.post("/api/auth/login", json={"email": email, "password": password})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 20

    def test_password_incorrecta_devuelve_401(self, client, db_session):
        email, _ = _create_admin(db_session)
        resp = client.post("/api/auth/login", json={"email": email, "password": "wrong"})
        assert resp.status_code == 401

    def test_usuario_inexistente_devuelve_401(self, client):
        resp = client.post("/api/auth/login", json={"email": "noexiste@test.com", "password": "pass"})
        assert resp.status_code == 401

    def test_campos_faltantes_devuelve_422(self, client):
        resp = client.post("/api/auth/login", json={"email": "admin@test.com"})
        assert resp.status_code == 422


class TestRutasProtegidas:
    def test_sin_token_stats_devuelve_401(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 401

    def test_token_invalido_devuelve_401(self, client):
        resp = client.get(
            "/api/admin/stats",
            headers={"Authorization": "Bearer token_inventado"},
        )
        assert resp.status_code == 401

    def test_con_token_valido_stats_devuelve_200(self, client, admin_token):
        resp = client.get(
            "/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
