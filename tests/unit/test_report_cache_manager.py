# -*- coding: utf-8 -*-
"""Tests for app/services/report_framework/cache_manager.py"""
import time
from unittest.mock import MagicMock, patch

from app.services.report_framework.cache_manager import (
    MemoryCacheBackend,
    RedisCacheBackend,
    ReportCacheManager,
)


class TestMemoryCacheBackend:
    def test_set_and_get(self):
        cache = MemoryCacheBackend()
        cache.set("key1", "value1", 300)
        assert cache.get("key1") == "value1"

    def test_get_missing(self):
        cache = MemoryCacheBackend()
        assert cache.get("missing") is None

    def test_expired(self):
        cache = MemoryCacheBackend()
        cache.set("key1", "value1", 1)
        # Manually expire
        cache._cache["key1"]["expires_at"] = time.time() - 1
        assert cache.get("key1") is None

    def test_no_ttl(self):
        cache = MemoryCacheBackend()
        cache.set("key1", "value1", 0)
        assert cache.get("key1") == "value1"

    def test_delete(self):
        cache = MemoryCacheBackend()
        cache.set("key1", "value1", 300)
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_missing(self):
        cache = MemoryCacheBackend()
        cache.delete("missing")  # should not raise

    def test_clear_all(self):
        cache = MemoryCacheBackend()
        cache.set("a", 1, 300)
        cache.set("b", 2, 300)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_clear_pattern(self):
        cache = MemoryCacheBackend()
        cache.set("report:a", 1, 300)
        cache.set("report:b", 2, 300)
        cache.set("other:c", 3, 300)
        cache.clear("report:*")
        assert cache.get("report:a") is None
        assert cache.get("other:c") == 3

    def test_cleanup_expired(self):
        cache = MemoryCacheBackend()
        cache.set("a", 1, 1)
        cache.set("b", 2, 300)
        cache._cache["a"]["expires_at"] = time.time() - 1
        count = cache.cleanup_expired()
        assert count == 1
        assert cache.get("a") is None
        assert cache.get("b") == 2


class TestRedisCacheBackend:
    def test_key_prefix(self):
        backend = RedisCacheBackend(prefix="test:")
        assert backend._key("foo") == "test:foo"

    def test_get_returns_none_on_error(self):
        backend = RedisCacheBackend()
        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("conn error")
        backend._redis = mock_redis
        assert backend.get("key") is None

    def test_set_ignores_error(self):
        backend = RedisCacheBackend()
        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("conn error")
        backend._redis = mock_redis
        backend.set("key", "val", 60)  # should not raise

    def test_get_returns_data(self):
        backend = RedisCacheBackend()
        mock_redis = MagicMock()
        mock_redis.get.return_value = '{"a": 1}'
        backend._redis = mock_redis
        assert backend.get("key") == {"a": 1}


class TestReportCacheManager:
    def _make_config(self, enabled=True, ttl=300, key_pattern=None):
        config = MagicMock()
        config.cache.enabled = enabled
        config.cache.ttl = ttl
        config.cache.key_pattern = key_pattern
        config.meta.code = "TEST"
        return config

    def test_get_disabled(self):
        mgr = ReportCacheManager()
        config = self._make_config(enabled=False)
        assert mgr.get(config, {}) is None

    def test_set_and_get(self):
        mgr = ReportCacheManager()
        config = self._make_config()
        mgr.set(config, {"year": 2026}, {"data": "result"})
        assert mgr.get(config, {"year": 2026}) == {"data": "result"}

    def test_set_disabled(self):
        mgr = ReportCacheManager()
        config = self._make_config(enabled=False)
        mgr.set(config, {}, "val")
        # no error

    def test_invalidate(self):
        mgr = ReportCacheManager()
        config = self._make_config()
        mgr.set(config, {"x": 1}, "data")
        mgr.invalidate("TEST")
        assert mgr.get(config, {"x": 1}) is None

    def test_clear_all(self):
        mgr = ReportCacheManager()
        config = self._make_config()
        mgr.set(config, {}, "data")
        mgr.clear_all()
        assert mgr.get(config, {}) is None

    def test_key_pattern(self):
        mgr = ReportCacheManager()
        config = self._make_config(key_pattern="custom:{code}:{year}")
        key = mgr._generate_key(config, {"year": 2026})
        assert key == "custom:TEST:2026"
