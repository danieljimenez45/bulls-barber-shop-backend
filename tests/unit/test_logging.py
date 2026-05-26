"""Tests del módulo de logging estructurado."""

import json
import logging

import pytest

from app.core.logging import _JSONFormatter, setup_logging


@pytest.mark.unit
def test_json_formatter_emite_linea_json():
    setup_logging(debug=False)
    formatter = _JSONFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="evento de prueba",
        args=(),
        exc_info=None,
    )
    line = formatter.format(record)
    data = json.loads(line)
    assert data["msg"] == "evento de prueba"
    assert data["level"] == "info"


@pytest.mark.unit
def test_setup_logging_debug_usa_formato_legible():
    setup_logging(debug=True)
    root = logging.getLogger()
    assert len(root.handlers) >= 1
