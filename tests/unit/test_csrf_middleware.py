# -*- coding: utf-8 -*-
"""
Comprehensive tests for app/core/csrf.py
Tests use unittest.mock to avoid importing the full app.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.csrf import (
    CSRFMiddleware,
    generate_csrf_token,
    verify_csrf_token,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(
    method="POST",
    path="/api/v1/something",
    headers=None,
    client_host="127.0.0.1",
    cookies=None,
):
    """Build a mock FastAPI/Starlette Request."""
    req = MagicMock()
    req.method = method
    req.url.path = path
    req.client.host = client_host
    _headers = {k.lower(): v for k, v in (headers or {}).items()}
    req.headers.get = lambda key, default=None: _headers.get(key.lower(), default)
    req.cookies = cookies or {}
    return req


def _make_middleware(debug=True):
    """Create a CSRFMiddleware instance with a dummy app."""
    with patch("app.core.csrf.settings") as mock_settings:
        mock_settings.DEBUG = debug
        mock_settings.CORS_ORIGINS = ["http://localhost:3000", "https://example.com"]
        app = MagicMock()
        mw = CSRFMiddleware(app)
        mw.csrf_enabled = not debug
        return mw


# ---------------------------------------------------------------------------
# generate_csrf_token / verify_csrf_token
# ---------------------------------------------------------------------------

class TestGenerateCsrfToken:
    def test_returns_string(self):
        token = generate_csrf_token()
        assert isinstance(token, str)

    def test_different_on_each_call(self):
        tokens = {generate_csrf_token() for _ in range(50)}
        assert len(tokens) == 50  # all unique

    def test_minimum_length(self):
        token = generate_csrf_token()
        assert len(token) >= 32


class TestVerifyCsrfToken:
    def test_matching_token(self):
        token = "secure_token_value"
        request = _make_request(cookies={"csrf_token": token})
        assert verify_csrf_token(request, token) is True

    def test_mismatching_token(self):
        request = _make_request(cookies={"csrf_token": "real_token"})
        assert verify_csrf_token(request, "wrong_token") is False

    def test_missing_cookie(self):
        request = _make_request(cookies={})
        assert verify_csrf_token(request, "some_token") is False

    def test_empty_both(self):
        request = _make_request(cookies={"csrf_token": ""})
        assert verify_csrf_token(request, "") is True


# ---------------------------------------------------------------------------
# CSRFMiddleware._is_exempt_path
# ---------------------------------------------------------------------------

class TestIsExemptPath:
    def setup_method(self):
        self.mw = _make_middleware()

    def test_login_is_exempt(self):
        assert self.mw._is_exempt_path("/api/v1/auth/login") is True

    def test_root_is_exempt(self):
        assert self.mw._is_exempt_path("/") is True

    def test_health_is_exempt(self):
        assert self.mw._is_exempt_path("/health") is True

    def test_docs_prefix_exempt(self):
        assert self.mw._is_exempt_path("/docs/something") is True

    def test_redoc_prefix_exempt(self):
        assert self.mw._is_exempt_path("/redoc/anything") is True

    def test_arbitrary_api_path_not_exempt(self):
        assert self.mw._is_exempt_path("/api/v1/users") is False

    def test_openapi_json_exempt(self):
        assert self.mw._is_exempt_path("/openapi.json") is True


# ---------------------------------------------------------------------------
# CSRFMiddleware._normalize_origin
# ---------------------------------------------------------------------------

class TestNormalizeOrigin:
    def setup_method(self):
        self.mw = _make_middleware()

    def test_removes_path(self):
        result = self.mw._normalize_origin("https://example.com/some/path")
        assert result == "https://example.com"

    def test_removes_trailing_slash(self):
        result = self.mw._normalize_origin("https://example.com/")
        assert result == "https://example.com"

    def test_removes_https_default_port(self):
        result = self.mw._normalize_origin("https://example.com:443")
        assert result == "https://example.com"

    def test_removes_http_default_port(self):
        result = self.mw._normalize_origin("http://example.com:80")
        assert result == "http://example.com"

    def test_keeps_non_default_port(self):
        result = self.mw._normalize_origin("http://localhost:3000")
        assert result == "http://localhost:3000"

    def test_empty_string(self):
        result = self.mw._normalize_origin("")
        assert result == ""


# ---------------------------------------------------------------------------
# CSRFMiddleware._is_origin_allowed
# ---------------------------------------------------------------------------

class TestIsOriginAllowed:
    def setup_method(self):
        self.mw = _make_middleware()

    @patch("app.core.csrf.settings")
    def test_exact_match_allowed(self, mock_settings):
        mock_settings.CORS_ORIGINS = ["http://localhost:3000"]
        mock_settings.DEBUG = False
        assert self.mw._is_origin_allowed("http://localhost:3000") is True

    @patch("app.core.csrf.settings")
    def test_not_in_list_denied(self, mock_settings):
        mock_settings.CORS_ORIGINS = ["http://localhost:3000"]
        mock_settings.DEBUG = False
        assert self.mw._is_origin_allowed("http://evil.com") is False

    @patch("app.core.csrf.settings")
    def test_wildcard_only_in_debug(self, mock_settings):
        mock_settings.CORS_ORIGINS = ["*"]
        mock_settings.DEBUG = True
        assert self.mw._is_origin_allowed("http://anything.com") is True

    @patch("app.core.csrf.settings")
    def test_wildcard_denied_in_production(self, mock_settings):
        mock_settings.CORS_ORIGINS = ["*"]
        mock_settings.DEBUG = False
        assert self.mw._is_origin_allowed("http://anything.com") is False

    @patch("app.core.csrf.settings")
    def test_empty_cors_origins_denies_all(self, mock_settings):
        mock_settings.CORS_ORIGINS = []
        mock_settings.DEBUG = False
        assert self.mw._is_origin_allowed("http://example.com") is False


# ---------------------------------------------------------------------------
# CSRFMiddleware._extract_origin_from_referer
# ---------------------------------------------------------------------------

class TestExtractOriginFromReferer:
    def setup_method(self):
        self.mw = _make_middleware()

    def test_extracts_from_full_url(self):
        result = self.mw._extract_origin_from_referer("https://example.com/page/1")
        assert result == "https://example.com"

    def test_none_returns_none(self):
        result = self.mw._extract_origin_from_referer(None)
        assert result is None

    def test_empty_returns_none(self):
        result = self.mw._extract_origin_from_referer("")
        assert result is None

    def test_with_port(self):
        result = self.mw._extract_origin_from_referer("http://localhost:3000/app")
        assert result == "http://localhost:3000"


# ---------------------------------------------------------------------------
# CSRFMiddleware.dispatch – safe methods pass through
# ---------------------------------------------------------------------------

class TestDispatchSafeMethods:
    @pytest.mark.asyncio
    async def test_get_request_passes_through(self):
        mw = _make_middleware(debug=True)
        request = _make_request(method="GET", path="/api/v1/users")
        next_response = MagicMock()
        mw._add_cors_headers = MagicMock()

        async def call_next(req):
            return next_response

        response = await mw.dispatch(request, call_next)
        assert response is next_response

    @pytest.mark.asyncio
    async def test_head_request_passes_through(self):
        mw = _make_middleware(debug=True)
        request = _make_request(method="HEAD", path="/api/v1/users")
        next_response = MagicMock()

        async def call_next(req):
            return next_response

        response = await mw.dispatch(request, call_next)
        assert response is next_response

    @pytest.mark.asyncio
    async def test_options_request_adds_cors_headers(self):
        mw = _make_middleware(debug=True)
        request = _make_request(method="OPTIONS", path="/api/v1/users")
        next_response = MagicMock()
        mw._add_cors_headers = MagicMock()

        async def call_next(req):
            return next_response

        response = await mw.dispatch(request, call_next)
        mw._add_cors_headers.assert_called_once()


# ---------------------------------------------------------------------------
# CSRFMiddleware.dispatch – exempt paths
# ---------------------------------------------------------------------------

class TestDispatchExemptPaths:
    @pytest.mark.asyncio
    async def test_login_path_exempt(self):
        mw = _make_middleware(debug=False)
        request = _make_request(method="POST", path="/api/v1/auth/login")
        next_response = MagicMock()

        async def call_next(req):
            return next_response

        response = await mw.dispatch(request, call_next)
        assert response is next_response


# ---------------------------------------------------------------------------
# CSRFMiddleware.dispatch – debug mode
# ---------------------------------------------------------------------------

class TestDispatchDebugMode:
    @pytest.mark.asyncio
    async def test_debug_mode_skips_csrf_check(self):
        """In DEBUG mode, all non-safe non-exempt requests should pass through."""
        mw = _make_middleware(debug=True)
        request = _make_request(
            method="POST",
            path="/api/v1/users",
            headers={},  # no Origin, no Authorization
        )
        next_response = MagicMock()

        async def call_next(req):
            return next_response

        with patch("app.core.csrf.settings") as ms:
            ms.DEBUG = True
            ms.CORS_ORIGINS = []
            response = await mw.dispatch(request, call_next)
        assert response is next_response


# ---------------------------------------------------------------------------
# CSRFMiddleware._validate_web_request
# ---------------------------------------------------------------------------

class TestValidateWebRequest:
    def test_debug_mode_returns_none(self):
        with patch("app.core.csrf.settings") as ms:
            ms.DEBUG = True
            mw = _make_middleware(debug=True)
            request = _make_request()
            # Should not raise
            mw._validate_web_request(request)

    def test_no_origin_or_referer_raises(self):
        from fastapi import HTTPException
        with patch("app.core.csrf.settings") as ms:
            ms.DEBUG = False
            mw = _make_middleware(debug=False)
            request = _make_request(headers={})
            with pytest.raises(HTTPException) as exc_info:
                mw._validate_web_request(request)
            assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# CSRFMiddleware._add_cors_headers
# ---------------------------------------------------------------------------

class TestAddCorsHeaders:
    def test_allowed_origin_sets_headers(self):
        mw = _make_middleware()
        mw._is_origin_allowed = MagicMock(return_value=True)
        request = _make_request(headers={"Origin": "http://localhost:3000"})
        response = MagicMock()
        response.headers = {}

        mw._add_cors_headers(response, request)

        assert "Access-Control-Allow-Origin" in response.headers

    def test_disallowed_origin_no_headers_set(self):
        mw = _make_middleware()
        mw._is_origin_allowed = MagicMock(return_value=False)
        request = _make_request(headers={"Origin": "http://evil.com"})
        response = MagicMock()
        response.headers = {}

        mw._add_cors_headers(response, request)
        assert "Access-Control-Allow-Origin" not in response.headers

    def test_no_origin_no_headers_set(self):
        mw = _make_middleware()
        request = _make_request(headers={})
        response = MagicMock()
        response.headers = {}

        mw._add_cors_headers(response, request)
        assert "Access-Control-Allow-Origin" not in response.headers
