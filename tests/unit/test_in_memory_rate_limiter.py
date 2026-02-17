# -*- coding: utf-8 -*-
"""
Tests for app/core/middleware/rate_limiting.py
Covers InMemoryRateLimiter and RateLimitMiddleware.
"""
import time
import threading
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.core.middleware.rate_limiting import InMemoryRateLimiter, RateLimitMiddleware, rate_limiter


# ---------------------------------------------------------------------------
# InMemoryRateLimiter
# ---------------------------------------------------------------------------

class TestInMemoryRateLimiter:
    def setup_method(self):
        self.limiter = InMemoryRateLimiter()

    def test_first_request_allowed(self):
        assert self.limiter.is_allowed("key1", limit=5, window=60) is True

    def test_within_limit_allowed(self):
        for _ in range(4):
            assert self.limiter.is_allowed("key2", limit=5, window=60) is True

    def test_exceeding_limit_denied(self):
        for _ in range(5):
            self.limiter.is_allowed("key3", limit=5, window=60)
        assert self.limiter.is_allowed("key3", limit=5, window=60) is False

    def test_different_keys_isolated(self):
        for _ in range(5):
            self.limiter.is_allowed("keyA", limit=5, window=60)
        # keyB should still be allowed
        assert self.limiter.is_allowed("keyB", limit=5, window=60) is True

    def test_expired_requests_dont_count(self):
        # Add stale timestamp directly
        import time
        with self.limiter._lock:
            self.limiter._requests["stale_key"] = [time.time() - 120] * 10
        # All are outside 60s window → request should be allowed
        assert self.limiter.is_allowed("stale_key", limit=5, window=60) is True

    def test_limit_1_allows_first(self):
        assert self.limiter.is_allowed("strict_key", limit=1, window=60) is True

    def test_limit_1_denies_second(self):
        self.limiter.is_allowed("strict_key2", limit=1, window=60)
        assert self.limiter.is_allowed("strict_key2", limit=1, window=60) is False

    def test_thread_safety(self):
        """Concurrent requests should not crash."""
        errors = []

        def make_requests():
            try:
                for _ in range(10):
                    self.limiter.is_allowed("concurrent_key", limit=100, window=60)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []


class TestGlobalRateLimiterSingleton:
    def test_is_instance(self):
        assert isinstance(rate_limiter, InMemoryRateLimiter)


# ---------------------------------------------------------------------------
# RateLimitMiddleware
# ---------------------------------------------------------------------------

def _make_request(path="/api/v1/data", client_host="127.0.0.1"):
    req = MagicMock()
    req.url.path = path
    req.client.host = client_host
    return req


class TestRateLimitMiddleware:
    def setup_method(self):
        """Fresh middleware with fresh limiter to avoid test pollution."""
        app = MagicMock()
        self.mw = RateLimitMiddleware(app)
        # Replace the global rate_limiter used by middleware
        self._fresh_limiter = InMemoryRateLimiter()
        import app.core.middleware.rate_limiting as mod
        self._orig_limiter = mod.rate_limiter
        mod.rate_limiter = self._fresh_limiter

    def teardown_method(self):
        import app.core.middleware.rate_limiting as mod
        mod.rate_limiter = self._orig_limiter

    @pytest.mark.asyncio
    async def test_normal_request_passes_through(self):
        req = _make_request(path="/api/v1/users")
        next_response = MagicMock()

        async def call_next(r):
            return next_response

        resp = await self.mw.dispatch(req, call_next)
        assert resp is next_response

    @pytest.mark.asyncio
    async def test_global_rate_limit_triggered(self):
        """After 300 requests from same IP, return 429."""
        # Exhaust global limit
        for _ in range(300):
            self._fresh_limiter.is_allowed("global:1.1.1.1", 300, 60)

        req = _make_request(client_host="1.1.1.1")

        async def call_next(r):
            return MagicMock()

        resp = await self.mw.dispatch(req, call_next)
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_login_rate_limit_triggered(self):
        """After 10 login attempts from same IP, return 429."""
        for _ in range(10):
            self._fresh_limiter.is_allowed("login:2.2.2.2", 10, 60)

        req = _make_request(path="/api/v1/auth/login", client_host="2.2.2.2")

        async def call_next(r):
            return MagicMock()

        resp = await self.mw.dispatch(req, call_next)
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_auth_token_path_limited(self):
        """Token endpoint is also subject to login rate limit."""
        for _ in range(10):
            self._fresh_limiter.is_allowed("login:3.3.3.3", 10, 60)

        req = _make_request(path="/api/v1/auth/token", client_host="3.3.3.3")

        async def call_next(r):
            return MagicMock()

        resp = await self.mw.dispatch(req, call_next)
        assert resp.status_code == 429

    @pytest.mark.asyncio
    async def test_no_client_uses_unknown(self):
        """Request with no client.host should use 'unknown'."""
        req = MagicMock()
        req.url.path = "/api/v1/users"
        req.client = None
        next_response = MagicMock()

        async def call_next(r):
            return next_response

        resp = await self.mw.dispatch(req, call_next)
        assert resp is next_response
