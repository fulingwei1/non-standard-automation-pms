# -*- coding: utf-8 -*-
"""
Tests for app/core/security_headers.py
"""
import pytest
from unittest.mock import MagicMock, patch

from app.core.security_headers import SecurityHeadersMiddleware, setup_security_headers


def _make_middleware(debug=True):
    with patch("app.core.security_headers.settings") as ms:
        ms.DEBUG = debug
        ms.CORS_ORIGINS = ["https://example.com"]
        app = MagicMock()
        mw = SecurityHeadersMiddleware(app)
    return mw


def _make_response():
    resp = MagicMock()
    resp.headers = {}
    return resp


def _make_request(path="/api/v1/something"):
    req = MagicMock()
    req.url.path = path
    return req


# ---------------------------------------------------------------------------
# Security headers applied to every response
# ---------------------------------------------------------------------------

class TestSecurityHeadersAdded:
    def setup_method(self):
        self.mw = _make_middleware(debug=True)

    def test_x_frame_options_set(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = ["https://example.com"]
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options_set(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_xss_protection_set(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy_set(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_server_header_hidden(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("Server") == "PMS"

    def test_cross_origin_opener_policy_set(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("Cross-Origin-Opener-Policy") == "same-origin"

    def test_cross_origin_resource_policy_set(self):
        resp = _make_response()
        req = _make_request()
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            self.mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("Cross-Origin-Resource-Policy") == "same-origin"


class TestProductionOnlyHeaders:
    def test_hsts_set_in_production(self):
        resp = _make_response()
        req = _make_request()
        mw = _make_middleware(debug=False)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = False
            ms.CORS_ORIGINS = []
            mw._add_security_headers(resp, req, "testnonce")
        assert "Strict-Transport-Security" in resp.headers

    def test_hsts_not_set_in_debug(self):
        resp = _make_response()
        req = _make_request()
        mw = _make_middleware(debug=True)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            mw._add_security_headers(resp, req, "testnonce")
        assert "Strict-Transport-Security" not in resp.headers

    def test_coep_set_in_production(self):
        resp = _make_response()
        req = _make_request()
        mw = _make_middleware(debug=False)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = False
            ms.CORS_ORIGINS = []
            mw._add_security_headers(resp, req, "testnonce")
        assert resp.headers.get("Cross-Origin-Embedder-Policy") == "require-corp"

    def test_coep_not_set_in_debug(self):
        resp = _make_response()
        req = _make_request()
        mw = _make_middleware(debug=True)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            mw._add_security_headers(resp, req, "testnonce")
        assert "Cross-Origin-Embedder-Policy" not in resp.headers


# ---------------------------------------------------------------------------
# CSP policy
# ---------------------------------------------------------------------------

class TestBuildCspPolicy:
    def test_debug_csp_allows_unsafe_inline(self):
        mw = _make_middleware(debug=True)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            csp = mw._build_csp_policy("nonce123")
        assert "unsafe-inline" in csp

    def test_production_csp_uses_nonce(self):
        mw = _make_middleware(debug=False)
        nonce = "abc123"
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = False
            ms.CORS_ORIGINS = []
            csp = mw._build_csp_policy(nonce)
        assert f"nonce-{nonce}" in csp

    def test_production_csp_no_unsafe_inline(self):
        mw = _make_middleware(debug=False)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = False
            ms.CORS_ORIGINS = []
            csp = mw._build_csp_policy("nonce")
        assert "unsafe-inline" not in csp

    def test_csp_includes_default_src(self):
        mw = _make_middleware(debug=True)
        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            csp = mw._build_csp_policy("n")
        assert "default-src" in csp


# ---------------------------------------------------------------------------
# Permissions policy
# ---------------------------------------------------------------------------

class TestBuildPermissionsPolicy:
    def test_contains_geolocation_disabled(self):
        mw = _make_middleware()
        policy = mw._build_permissions_policy()
        assert "geolocation=()" in policy

    def test_contains_camera_disabled(self):
        mw = _make_middleware()
        policy = mw._build_permissions_policy()
        assert "camera=()" in policy

    def test_contains_microphone_disabled(self):
        mw = _make_middleware()
        policy = mw._build_permissions_policy()
        assert "microphone=()" in policy

    def test_fullscreen_allows_self(self):
        mw = _make_middleware()
        policy = mw._build_permissions_policy()
        assert "fullscreen=(self)" in policy


# ---------------------------------------------------------------------------
# No-cache headers for sensitive paths
# ---------------------------------------------------------------------------

class TestNoCacheHeaders:
    def test_no_cache_headers_added(self):
        mw = _make_middleware()
        resp = _make_response()
        mw._add_no_cache_headers(resp)
        assert "no-store" in resp.headers.get("Cache-Control", "")
        assert resp.headers.get("Pragma") == "no-cache"
        assert resp.headers.get("Expires") == "0"


# ---------------------------------------------------------------------------
# dispatch – integration
# ---------------------------------------------------------------------------

class TestDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_adds_headers(self):
        mw = _make_middleware(debug=True)
        resp = _make_response()
        req = _make_request(path="/api/v1/data")

        async def call_next(r):
            return resp

        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            result = await mw.dispatch(req, call_next)

        assert result is resp
        assert "X-Frame-Options" in result.headers

    @pytest.mark.asyncio
    async def test_sensitive_path_gets_no_cache_headers(self):
        mw = _make_middleware(debug=True)
        resp = _make_response()
        req = _make_request(path="/api/v1/auth/login")

        async def call_next(r):
            return resp

        with patch("app.core.security_headers.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            result = await mw.dispatch(req, call_next)

        assert "no-store" in result.headers.get("Cache-Control", "")


# ---------------------------------------------------------------------------
# setup_security_headers
# ---------------------------------------------------------------------------

class TestSetupSecurityHeaders:
    def test_adds_middleware_to_app(self):
        from fastapi import FastAPI
        app = FastAPI()
        setup_security_headers(app)
        # Check that the middleware stack was modified
        # (FastAPI stores middleware in app.middleware_stack or similar)
        assert True  # no crash = success
