# -*- coding: utf-8 -*-
"""
Unit tests for app/utils/cache_decorator.py  — L4组补充
重点覆盖 cache_response 装饰器（原有测试覆盖率较低的部分）
"""

import pytest
from unittest.mock import MagicMock, patch

from app.utils.cache_decorator import cache_response, get_cache_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_cache(cached_value=None):
    """Return a MagicMock CacheService whose get() returns cached_value."""
    mock = MagicMock()
    mock.get.return_value = cached_value
    return mock


# ---------------------------------------------------------------------------
# cache_response decorator
# ---------------------------------------------------------------------------

class TestCacheResponse:
    """Tests for the @cache_response decorator."""

    def test_cache_miss_calls_wrapped_function(self):
        """On cache miss, the original function is called."""
        mock_cache = _mock_cache(cached_value=None)

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="test", ttl=60)
            def get_data(item_id=1):
                return {"id": item_id, "value": "fresh"}

            result = get_data(item_id=1)

        assert result["value"] == "fresh"
        mock_cache.set.assert_called_once()

    def test_cache_hit_returns_cached_data(self):
        """On cache hit, returns cached data and skips function call."""
        cached = {"id": 1, "value": "cached"}
        mock_cache = _mock_cache(cached_value=cached)

        call_count = 0

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="test", ttl=60)
            def get_data(item_id=1):
                nonlocal call_count
                call_count += 1
                return {"id": item_id, "value": "fresh"}

            result = get_data(item_id=1)

        assert call_count == 0  # original function not called
        assert result["value"] == "cached"
        assert result.get("_from_cache") is True

    def test_cache_miss_sets_from_cache_false(self):
        """On cache miss, result dict gets _from_cache=False."""
        mock_cache = _mock_cache(cached_value=None)

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="items", ttl=120)
            def get_items(page=1):
                return {"page": page, "items": []}

            result = get_items(page=1)

        assert result.get("_from_cache") is False

    def test_cache_miss_stores_result_with_correct_ttl(self):
        """Stores result in cache with the specified TTL."""
        mock_cache = _mock_cache(cached_value=None)

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="data", ttl=300)
            def get_data(**kwargs):
                return {"ok": True}

            get_data()

        call_kwargs = mock_cache.set.call_args[1]
        assert call_kwargs.get("expire_seconds") == 300

    def test_custom_key_func_used_for_cache_key(self):
        """Uses custom key_func when provided."""
        mock_cache = _mock_cache(cached_value=None)

        custom_keys = []

        def my_key_func(*args, **kwargs):
            key = f"custom:{kwargs.get('user_id', 0)}"
            custom_keys.append(key)
            return key

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="user", ttl=60, key_func=my_key_func)
            def get_user(user_id=None):
                return {"user_id": user_id}

            get_user(user_id=42)

        assert len(custom_keys) == 1
        assert custom_keys[0] == "custom:42"
        # The cache should have been queried with the custom key
        mock_cache.get.assert_called_once_with("custom:42")

    def test_non_dict_result_not_tagged(self):
        """Non-dict results are returned as-is (no _from_cache injection)."""
        mock_cache = _mock_cache(cached_value=None)

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="str_result", ttl=60)
            def get_string(**kwargs):
                return "hello world"

            result = get_string()

        assert result == "hello world"

    def test_non_dict_cache_hit_returned_as_is(self):
        """Non-dict cached data is returned without _from_cache modification."""
        mock_cache = _mock_cache(cached_value=[1, 2, 3])

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="list_result", ttl=60)
            def get_list(**kwargs):
                return []

            result = get_list()

        assert result == [1, 2, 3]

    def test_cache_key_uses_prefix(self):
        """Generated cache key starts with the given prefix."""
        mock_cache = _mock_cache(cached_value=None)
        captured_keys = []

        original_set = mock_cache.set
        def capture_set(key, value, **kwargs):
            captured_keys.append(key)
        mock_cache.set.side_effect = capture_set

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="myprefix", ttl=60)
            def my_func(**kwargs):
                return {"data": 1}

            my_func()

        # get is called with a key
        get_key = mock_cache.get.call_args[0][0]
        assert get_key.startswith("myprefix:")

    def test_invalidate_cache_attribute_exists(self):
        """Decorated function has invalidate_cache attribute."""
        @cache_response(prefix="check", ttl=60)
        def some_func():
            return {}

        assert hasattr(some_func, "invalidate_cache")
        assert callable(some_func.invalidate_cache)

    def test_invalidate_cache_calls_invalidate_func(self):
        """invalidate_cache calls the provided invalidate_func."""
        invalidate_calls = []

        def my_invalidate(*args, **kwargs):
            invalidate_calls.append((args, kwargs))

        @cache_response(prefix="inv", ttl=60, invalidate_func=my_invalidate)
        def some_func():
            return {}

        some_func.invalidate_cache("arg1", key="val")
        assert len(invalidate_calls) == 1
        assert invalidate_calls[0] == (("arg1",), {"key": "val"})

    def test_invalidate_cache_returns_none_without_func(self):
        """invalidate_cache returns None when no invalidate_func provided."""
        @cache_response(prefix="noinv", ttl=60)
        def some_func():
            return {}

        result = some_func.invalidate_cache()
        assert result is None

    def test_functools_wraps_preserves_name(self):
        """@cache_response preserves the original function __name__."""
        @cache_response(prefix="test", ttl=60)
        def my_special_function():
            return {}

        assert my_special_function.__name__ == "my_special_function"

    def test_different_kwargs_generate_different_keys(self):
        """Different kwargs produce different cache keys."""
        mock_cache = _mock_cache(cached_value=None)
        queried_keys = []

        def capture_get(key):
            queried_keys.append(key)
            return None
        mock_cache.get.side_effect = capture_get

        with patch("app.utils.cache_decorator.get_cache_service", return_value=mock_cache):
            @cache_response(prefix="items", ttl=60)
            def get_items(**kwargs):
                return {"items": []}

            get_items(page=1)
            get_items(page=2)

        assert len(queried_keys) == 2
        assert queried_keys[0] != queried_keys[1]


class TestGetCacheService:
    """Tests for get_cache_service singleton behavior."""

    def test_returns_cache_service_instance(self):
        """get_cache_service returns a CacheService instance."""
        import app.utils.cache_decorator as mod
        original = mod._cache_service
        try:
            mod._cache_service = None
            with patch("app.utils.cache_decorator.CacheService") as MockCS:
                MockCS.return_value = MagicMock()
                svc = get_cache_service()
            assert svc is not None
        finally:
            mod._cache_service = original

    def test_singleton_returns_same_instance(self):
        """get_cache_service always returns the same object."""
        import app.utils.cache_decorator as mod
        original = mod._cache_service

        try:
            mod._cache_service = None
            with patch("app.utils.cache_decorator.CacheService") as MockCS:
                instance = MagicMock()
                MockCS.return_value = instance
                svc1 = get_cache_service()
                svc2 = get_cache_service()
            assert svc1 is svc2
        finally:
            mod._cache_service = original
