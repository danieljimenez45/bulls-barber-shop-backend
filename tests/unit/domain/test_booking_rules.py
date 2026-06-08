"""Tests de reglas de negocio de reservas."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.booking.rules import (
    FechaEnPasado,
    SlotFueraDeGrid,
    assert_future_datetime,
    assert_slot_en_grid,
)


# ── assert_future_datetime ─────────────────────────────────────────────────────

@pytest.mark.unit
def test_assert_future_datetime_acepta_futuro():
    futuro = datetime.now(timezone.utc) + timedelta(days=1)
    assert_future_datetime(futuro)


@pytest.mark.unit
def test_assert_future_datetime_rechaza_pasado():
    pasado = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(FechaEnPasado):
        assert_future_datetime(pasado, now=datetime.now(timezone.utc))


@pytest.mark.unit
def test_assert_future_datetime_rechaza_exactamente_ahora():
    ahora = datetime.now(timezone.utc)
    with pytest.raises(FechaEnPasado):
        assert_future_datetime(ahora, now=ahora)


# ── assert_slot_en_grid ────────────────────────────────────────────────────────

@pytest.mark.unit
def test_assert_slot_en_grid_en_punto_valido():
    assert_slot_en_grid(datetime(2030, 6, 1, 10, 0))  # no lanza


@pytest.mark.unit
def test_assert_slot_en_grid_y_media_valido():
    assert_slot_en_grid(datetime(2030, 6, 1, 10, 30))  # no lanza


@pytest.mark.unit
def test_assert_slot_en_grid_cuarto_invalido():
    with pytest.raises(SlotFueraDeGrid):
        assert_slot_en_grid(datetime(2030, 6, 1, 10, 15))


@pytest.mark.unit
def test_assert_slot_en_grid_tres_cuartos_invalido():
    with pytest.raises(SlotFueraDeGrid):
        assert_slot_en_grid(datetime(2030, 6, 1, 10, 45))


@pytest.mark.unit
def test_assert_slot_en_grid_un_minuto_invalido():
    with pytest.raises(SlotFueraDeGrid):
        assert_slot_en_grid(datetime(2030, 6, 1, 10, 1))


@pytest.mark.unit
def test_assert_slot_en_grid_mensaje_contiene_hora():
    """El mensaje de error debe incluir la hora recibida."""
    try:
        assert_slot_en_grid(datetime(2030, 6, 1, 10, 15))
    except SlotFueraDeGrid as exc:
        assert "10:15" in str(exc)
