"""Tests unitarios del módulo de rate limiting."""

import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.rate_limit import _get_client_ip, _store, limiter


def _make_request(ip="1.2.3.4", path="/test", forwarded_for=None):
    req = MagicMock()
    req.client.host = ip
    req.url.path = path
    headers = {}
    if forwarded_for:
        headers["X-Forwarded-For"] = forwarded_for
    req.headers.get = lambda k, d=None: headers.get(k, d)
    return req


class TestGetClientIp:
    def test_devuelve_ip_directa(self):
        req = _make_request(ip="10.0.0.1")
        assert _get_client_ip(req) == "10.0.0.1"

    def test_no_trusts_forwarded_for_by_default(self):
        import app.config as cfg

        cfg.settings.TRUST_PROXY_HEADERS = False
        req = _make_request(ip="10.0.0.1", forwarded_for="203.0.113.1, 10.0.0.1")
        assert _get_client_ip(req) == "10.0.0.1"

    def test_usa_x_forwarded_for_con_trust_proxy(self):
        import app.config as cfg

        cfg.settings.TRUST_PROXY_HEADERS = True
        req = _make_request(forwarded_for="203.0.113.1, 10.0.0.1")
        assert _get_client_ip(req) == "203.0.113.1"
        cfg.settings.TRUST_PROXY_HEADERS = False

    def test_sin_client(self):
        req = MagicMock()
        req.client = None
        req.headers.get = lambda k, d=None: None
        assert _get_client_ip(req) == "unknown"


class TestLimiter:
    def setup_method(self):
        _store.clear()
        # pytest.ini desactiva rate limit para integración; estos tests lo necesitan activo.
        import app.config as cfg
        cfg.settings.RATE_LIMIT_ENABLED = True

    def test_permite_peticiones_dentro_del_limite(self):
        import asyncio
        check = limiter(max_requests=3, window_seconds=60)
        req = _make_request()
        for _ in range(3):
            asyncio.run(check(req))

    def test_bloquea_al_superar_limite(self):
        import asyncio
        check = limiter(max_requests=2, window_seconds=60)
        req = _make_request()
        asyncio.run(check(req))
        asyncio.run(check(req))
        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(check(req))
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers

    def test_ips_distintas_tienen_contadores_independientes(self):
        import asyncio
        check = limiter(max_requests=1, window_seconds=60)
        asyncio.run(check(_make_request(ip="1.1.1.1")))
        asyncio.run(check(_make_request(ip="2.2.2.2")))

    def test_deshabilitado_no_bloquea(self):
        import asyncio
        import app.config as cfg
        cfg.settings.RATE_LIMIT_ENABLED = False
        check = limiter(max_requests=1, window_seconds=60)
        req = _make_request()
        for _ in range(10):
            asyncio.run(check(req))
        cfg.settings.RATE_LIMIT_ENABLED = True
