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

    def test_usa_x_forwarded_for(self):
        req = _make_request(forwarded_for="203.0.113.1, 10.0.0.1")
        assert _get_client_ip(req) == "203.0.113.1"

    def test_sin_client(self):
        req = MagicMock()
        req.client = None
        req.headers.get = lambda k, d=None: None
        assert _get_client_ip(req) == "unknown"


class TestLimiter:
    def setup_method(self):
        _store.clear()

    def test_permite_peticiones_dentro_del_limite(self):
        check = limiter(max_requests=3, window_seconds=60)
        req = _make_request()
        import asyncio
        for _ in range(3):
            asyncio.get_event_loop().run_until_complete(check(req))

    def test_bloquea_al_superar_limite(self):
        check = limiter(max_requests=2, window_seconds=60)
        req = _make_request()
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(check(req))
        loop.run_until_complete(check(req))
        with pytest.raises(HTTPException) as exc_info:
            loop.run_until_complete(check(req))
        assert exc_info.value.status_code == 429
        assert "Retry-After" in exc_info.value.headers

    def test_ips_distintas_tienen_contadores_independientes(self):
        check = limiter(max_requests=1, window_seconds=60)
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(check(_make_request(ip="1.1.1.1")))
        loop.run_until_complete(check(_make_request(ip="2.2.2.2")))

    def test_deshabilitado_no_bloquea(self):
        import app.config as cfg
        cfg.settings.RATE_LIMIT_ENABLED = False
        check = limiter(max_requests=1, window_seconds=60)
        req = _make_request()
        import asyncio
        loop = asyncio.get_event_loop()
        for _ in range(10):
            loop.run_until_complete(check(req))
        cfg.settings.RATE_LIMIT_ENABLED = True
