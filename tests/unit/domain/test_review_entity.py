"""Tests unitarios de la entidad Review (dominio puro, sin dependencias externas)."""

import pytest

from app.domain.review.entity import Review


# ── Validación de valoración ────────────────────────────────────────────────────

@pytest.mark.unit
def test_valoracion_valida():
    r = Review(nombre="Ana", valoracion=5)
    assert r.valoracion == 5


@pytest.mark.unit
def test_valoracion_minima():
    r = Review(nombre="Ana", valoracion=1)
    assert r.valoracion == 1


@pytest.mark.unit
def test_valoracion_cero_lanza_value_error():
    with pytest.raises(ValueError):
        Review(nombre="Ana", valoracion=0)


@pytest.mark.unit
def test_valoracion_seis_lanza_value_error():
    with pytest.raises(ValueError):
        Review(nombre="Ana", valoracion=6)


# ── Visibilidad ─────────────────────────────────────────────────────────────────

@pytest.mark.unit
def test_visible_por_defecto():
    r = Review(nombre="Ana", valoracion=4)
    assert r.visible is True


@pytest.mark.unit
def test_ocultar_cambia_visible_a_false():
    r = Review(nombre="Ana", valoracion=4)
    r.ocultar()
    assert r.visible is False


@pytest.mark.unit
def test_mostrar_restaura_visible_a_true():
    r = Review(nombre="Ana", valoracion=4)
    r.ocultar()
    r.mostrar()
    assert r.visible is True
