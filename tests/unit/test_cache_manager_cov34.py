# -*- coding: utf-8 -*-
"""报表缓存管理器单元测试 - 第三十四批"""

import pytest
import time
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.report_framework.cache_manager")

try:
    from app.services.report_framework.cache_manager import (
        MemoryCacheBackend,
        RedisCacheBackend,
        ReportCacheManager,
        CacheManager,
    )
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    MemoryCacheBackend = RedisCacheBackend = ReportCacheManager = CacheManager = None


class TestMemoryCacheBackend:
    def test_set_and_get(self):
        backend = MemoryCacheBackend()
        backend.set("key1", {"data": 42}, ttl=60)
        assert backend.get("key1") == {"data": 42}

    def test_get_missing_returns_none(self):
        backend = MemoryCacheBackend()
        assert backend.get("nonexistent") is None

    def test_delete_removes_key(self):
        backend = MemoryCacheBackend()
        backend.set("key2", "value", ttl=60)
        backend.delete("key2")
        assert backend.get("key2") is None

    def test_clear_all(self):
        backend = MemoryCacheBackend()
        backend.set("k1", 1, ttl=60)
        backend.set("k2", 2, ttl=60)
        backend.clear()
        assert backend.get("k1") is None
        assert backend.get("k2") is None

    def test_clear_with_pattern(self):
        backend = MemoryCacheBackend()
        backend.set("report:abc:1", "a", ttl=60)
        backend.set("report:abc:2", "b", ttl=60)
        backend.set("other:key", "c", ttl=60)
        backend.clear("report:abc:*")
        assert backend.get("report:abc:1") is None
        assert backend.get("report:abc:2") is None
        assert backend.get("other:key") == "c"

    def test_expired_returns_none(self):
        backend = MemoryCacheBackend()
        backend.set("expiring", "soon", ttl=1)
        # Force expire by manipulating internal cache
        backend._cache["expiring"]["expires_at"] = time.time() - 1
        assert backend.get("expiring") is None

    def test_cleanup_expired(self):
        backend = MemoryCacheBackend()
        backend.set("e1", "x", ttl=1)
        backend._cache["e1"]["expires_at"] = time.time() - 1
        count = backend.cleanup_expired()
        assert count == 1


class TestReportCacheManager:
    def _make_config(self, enabled=True, ttl=300, code="rpt01", key_pattern=None):
        config = MagicMock()
        config.cache.enabled = enabled
        config.cache.ttl = ttl
        config.cache.key_pattern = key_pattern
        config.meta.code = code
        return config

    def test_get_returns_none_when_cache_disabled(self):
        manager = ReportCacheManager()
        config = self._make_config(enabled=False)
        assert manager.get(config, {}) is None

    def test_set_and_get(self):
        manager = ReportCacheManager()
        config = self._make_config(enabled=True)
        manager.set(config, {"month": "2024-01"}, {"rows": 10})
        result = manager.get(config, {"month": "2024-01"})
        assert result == {"rows": 10}

    def test_different_params_different_keys(self):
        manager = ReportCacheManager()
        config = self._make_config(enabled=True)
        manager.set(config, {"month": "2024-01"}, "result_A")
        manager.set(config, {"month": "2024-02"}, "result_B")
        assert manager.get(config, {"month": "2024-01"}) == "result_A"
        assert manager.get(config, {"month": "2024-02"}) == "result_B"

    def test_invalidate_clears_report_cache(self):
        manager = ReportCacheManager()
        config = self._make_config(enabled=True, code="sales")
        manager.set(config, {"p": 1}, "data")
        manager.invalidate("sales")
        assert manager.get(config, {"p": 1}) is None

    def test_cache_manager_alias(self):
        assert CacheManager is ReportCacheManager
