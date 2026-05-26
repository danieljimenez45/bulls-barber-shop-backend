"""Tests de reglas de negocio de reservas."""

from datetime import datetime, timedelta, timezone

import pytest

from app.domain.booking.rules import FechaEnPasado, assert_future_datetime


@pytest.mark.unit
def test_assert_future_datetime_acepta_futuro():
    futuro = datetime.now(timezone.utc) + timedelta(days=1)
    assert_future_datetime(futuro)


@pytest.mark.unit
def test_assert_future_datetime_rechaza_pasado():
    pasado = datetime.now(timezone.utc) - timedelta(hours=1)
    with pytest.raises(FechaEnPasado):
        assert_future_datetime(pasado, now=datetime.now(timezone.utc))
