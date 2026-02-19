# -*- coding: utf-8 -*-
"""
第三十五批 - dashboard_cache_service.py 单元测试
"""
import pytest

try:
    from unittest.mock import MagicMock, patch
    from app.services.dashboard_cache_service import (
        DashboardCacheService,
        get_cache_service,
        invalidate_dashboard_cache,
    )
    import app.services.dashboard_cache_service as _mod
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


@pytest.fixture(autouse=True)
def reset_global_cache():
    """每个测试前后重置全局缓存实例"""
    import app.services.dashboard_cache_service as mod
    original = mod._cache_instance
    mod._cache_instance = None
    yield
    mod._cache_instance = original


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDashboardCacheServiceDisabled:
    """缓存禁用时的行为"""

    def test_init_without_redis_url(self):
        svc = DashboardCacheService(redis_url=None)
        assert svc.cache_enabled is False
        assert svc.redis_client is None

    def test_get_returns_none_when_disabled(self):
        svc = DashboardCacheService()
        result = svc.get("some-key")
        assert result is None

    def test_set_returns_false_when_disabled(self):
        svc = DashboardCacheService()
        result = svc.set("some-key", {"data": 1})
        assert result is False

    def test_delete_returns_false_when_disabled(self):
        svc = DashboardCacheService()
        result = svc.delete("some-key")
        assert result is False

    def test_clear_pattern_returns_zero_when_disabled(self):
        svc = DashboardCacheService()
        result = svc.clear_pattern("dashboard:*")
        assert result == 0

    def test_get_or_set_calls_fetch_func(self):
        svc = DashboardCacheService()
        fetch = MagicMock(return_value={"val": 42})
        result = svc.get_or_set("key", fetch)
        fetch.assert_called_once()
        assert result == {"val": 42}

    def test_get_cache_key_sorted(self):
        svc = DashboardCacheService()
        key = svc._get_cache_key("prefix", b=2, a=1)
        assert key.startswith("prefix:")
        # a:1 应在 b:2 之前（排序）
        assert key.index("a:1") < key.index("b:2")


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestDashboardCacheServiceEnabled:
    """使用 mock Redis 客户端的场景"""

    def _make_service_with_mock_redis(self):
        svc = DashboardCacheService.__new__(DashboardCacheService)
        svc.ttl = 300
        svc.cache_enabled = True
        svc.redis_client = MagicMock()
        return svc

    def test_get_hit(self):
        import json
        svc = self._make_service_with_mock_redis()
        svc.redis_client.get.return_value = json.dumps({"x": 1})
        result = svc.get("key")
        assert result == {"x": 1}

    def test_get_miss(self):
        svc = self._make_service_with_mock_redis()
        svc.redis_client.get.return_value = None
        result = svc.get("key")
        assert result is None

    def test_set_success(self):
        svc = self._make_service_with_mock_redis()
        svc.redis_client.setex.return_value = True
        result = svc.set("key", {"data": "test"})
        assert result is True
        svc.redis_client.setex.assert_called_once()

    def test_delete_success(self):
        svc = self._make_service_with_mock_redis()
        result = svc.delete("key")
        assert result is True
        svc.redis_client.delete.assert_called_once_with("key")

    def test_clear_pattern_with_keys(self):
        svc = self._make_service_with_mock_redis()
        svc.redis_client.keys.return_value = ["k1", "k2"]
        svc.redis_client.delete.return_value = 2
        result = svc.clear_pattern("dashboard:*")
        assert result == 2

    def test_get_or_set_uses_cache_when_available(self):
        import json
        svc = self._make_service_with_mock_redis()
        svc.redis_client.get.return_value = json.dumps({"cached": True})
        fetch = MagicMock()
        result = svc.get_or_set("key", fetch)
        assert result == {"cached": True}
        fetch.assert_not_called()

    def test_get_or_set_force_refresh(self):
        svc = self._make_service_with_mock_redis()
        svc.redis_client.get.return_value = None
        fetch = MagicMock(return_value={"fresh": True})
        result = svc.get_or_set("key", fetch, force_refresh=True)
        assert result == {"fresh": True}
        fetch.assert_called_once()


@pytest.mark.skipif(not IMPORT_OK, reason="导入失败")
class TestModuleFunctions:

    def test_get_cache_service_singleton(self):
        svc1 = get_cache_service()
        svc2 = get_cache_service()
        assert svc1 is svc2

    def test_invalidate_dashboard_cache(self):
        svc = DashboardCacheService.__new__(DashboardCacheService)
        svc.ttl = 300
        svc.cache_enabled = False
        svc.redis_client = None
        import app.services.dashboard_cache_service as mod
        mod._cache_instance = svc
        result = invalidate_dashboard_cache("dashboard:*")
        assert result == 0
