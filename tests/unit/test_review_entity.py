"""Tests unitarios de la entidad Review."""

import pytest

from app.domain.review.entity import Review


class TestReviewEntity:
    def test_valoracion_valida(self):
        r = Review(nombre="Ana", valoracion=5)
        assert r.valoracion == 5

    def test_valoracion_minima(self):
        r = Review(nombre="Ana", valoracion=1)
        assert r.valoracion == 1

    def test_valoracion_cero_lanza_error(self):
        with pytest.raises(ValueError):
            Review(nombre="Ana", valoracion=0)

    def test_valoracion_seis_lanza_error(self):
        with pytest.raises(ValueError):
            Review(nombre="Ana", valoracion=6)

    def test_visible_por_defecto(self):
        r = Review(nombre="Ana", valoracion=4)
        assert r.visible is True

    def test_ocultar(self):
        r = Review(nombre="Ana", valoracion=4)
        r.ocultar()
        assert r.visible is False

    def test_mostrar(self):
        r = Review(nombre="Ana", valoracion=4)
        r.ocultar()
        r.mostrar()
        assert r.visible is True
