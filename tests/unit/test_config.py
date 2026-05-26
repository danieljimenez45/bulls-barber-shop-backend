"""Tests de configuración (Settings)."""

import pytest
from pydantic import ValidationError

from app.config import Settings


@pytest.mark.unit
def test_secret_key_vacia_lanza_error():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(SECRET_KEY="")


@pytest.mark.unit
def test_parse_cors_origins_desde_string_csv():
    s = Settings(
        SECRET_KEY="test-secret-key-min-32-chars-long!!",
        CORS_ORIGINS="https://a.com, https://b.com",
    )
    assert s.CORS_ORIGINS == ["https://a.com", "https://b.com"]


@pytest.mark.unit
def test_parse_cors_origins_desde_json():
    s = Settings(
        SECRET_KEY="test-secret-key-min-32-chars-long!!",
        CORS_ORIGINS='["https://x.com"]',
    )
    assert s.CORS_ORIGINS == ["https://x.com"]


@pytest.mark.unit
def test_cloudinary_enabled_solo_con_tres_credenciales():
    base = {"SECRET_KEY": "test-secret-key-min-32-chars-long!!"}
    assert Settings(**base).cloudinary_enabled is False
    assert Settings(
        **base,
        CLOUDINARY_CLOUD_NAME="c",
        CLOUDINARY_API_KEY="k",
        CLOUDINARY_API_SECRET="s",
    ).cloudinary_enabled is True


@pytest.mark.unit
def test_get_cors_origins_anade_dominio_produccion():
    s = Settings(
        SECRET_KEY="test-secret-key-min-32-chars-long!!",
        PRODUCTION_DOMAIN="bullsbarbershop.es",
    )
    origins = s.get_cors_origins()
    assert "https://bullsbarbershop.es" in origins
    assert "http://bullsbarbershop.es" in origins
