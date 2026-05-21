"""Tests de integración para el endpoint /api/gallery."""

from unittest.mock import MagicMock, patch


class TestListarImagenes:
    def test_lista_vacia_inicialmente(self, client):
        resp = client.get("/api/gallery/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_paginacion_por_defecto(self, client):
        resp = client.get("/api/gallery/")
        data = resp.json()
        assert data["page"] == 1
        assert data["size"] == 20

    def test_paginacion_personalizada(self, client, admin_token, db_session):
        """Inserta imágenes directamente en BD para evitar dependencia de storage."""
        from app.infrastructure.persistence.orm.gallery import GalleryORM

        for i in range(3):
            db_session.add(GalleryORM(
                imagen_url=f"/uploads/img{i}.jpg",
                titulo=f"Imagen {i}",
                categoria="corte",
                visible=True,
            ))
        db_session.commit()

        resp = client.get("/api/gallery/?page=1&size=2")
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 3
        assert data["pages"] == 2

    def test_filtra_por_categoria(self, client, db_session):
        from app.infrastructure.persistence.orm.gallery import GalleryORM

        db_session.add(GalleryORM(imagen_url="/uploads/corte.jpg", categoria="corte", visible=True))
        db_session.add(GalleryORM(imagen_url="/uploads/barba.jpg", categoria="barba", visible=True))
        db_session.commit()

        resp = client.get("/api/gallery/?categoria=barba")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["categoria"] == "barba"

    def test_imagenes_no_visibles_no_aparecen(self, client, db_session):
        from app.infrastructure.persistence.orm.gallery import GalleryORM

        db_session.add(GalleryORM(imagen_url="/uploads/visible.jpg", categoria="corte", visible=True))
        db_session.add(GalleryORM(imagen_url="/uploads/oculta.jpg", categoria="corte", visible=False))
        db_session.commit()

        resp = client.get("/api/gallery/")
        assert resp.json()["total"] == 1


class TestSubirImagen:
    def test_sin_token_devuelve_401(self, client):
        resp = client.post(
            "/api/gallery/upload",
            files={"file": ("test.jpg", b"fake-image", "image/jpeg")},
        )
        assert resp.status_code == 401

    def test_sube_imagen_con_token(self, client, admin_token):
        mock_storage = MagicMock()
        mock_storage.save.return_value = "/uploads/test.jpg"

        with patch(
            "app.api.routers.gallery.LocalFileStorage",
            return_value=mock_storage,
        ):
            resp = client.post(
                "/api/gallery/upload",
                files={"file": ("foto.jpg", b"\xff\xd8\xff", "image/jpeg")},
                data={"titulo": "Mi foto", "categoria": "corte"},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["categoria"] == "corte"
        assert data["titulo"] == "Mi foto"


class TestEliminarImagen:
    def test_sin_token_devuelve_401(self, client, db_session):
        from app.infrastructure.persistence.orm.gallery import GalleryORM

        img = GalleryORM(imagen_url="/uploads/del.jpg", categoria="corte", visible=True)
        db_session.add(img)
        db_session.commit()
        db_session.refresh(img)

        resp = client.delete(f"/api/gallery/{img.id}")
        assert resp.status_code == 401

    def test_id_inexistente_devuelve_404(self, client, admin_token):
        mock_storage = MagicMock()
        with patch("app.api.routers.gallery.LocalFileStorage", return_value=mock_storage):
            resp = client.delete(
                "/api/gallery/9999",
                headers={"Authorization": f"Bearer {admin_token}"},
            )
        assert resp.status_code == 404
