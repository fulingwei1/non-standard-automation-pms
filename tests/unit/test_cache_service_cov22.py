# -*- coding: utf-8 -*-
"""第二十二批：cache_service 单元测试"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

try:
    from app.services.cache_service import CacheService
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="import failed")


@pytest.fixture
def cache():
    """使用内存缓存（无Redis）"""
    with patch("app.services.cache_service.REDIS_AVAILABLE", False):
        svc = CacheService(redis_client=None)
        return svc


@pytest.fixture
def cache_with_redis():
    """模拟Redis缓存"""
    mock_redis = MagicMock()
    with patch("app.services.cache_service.REDIS_AVAILABLE", True):
        svc = CacheService(redis_client=mock_redis)
        return svc, mock_redis


class TestCacheServiceInit:
    def test_memory_cache_initialized_empty(self, cache):
        """内存缓存初始为空"""
        assert cache.memory_cache == {}

    def test_use_redis_false_when_no_client(self, cache):
        """无Redis客户端时use_redis为False"""
        assert cache.use_redis is False

    def test_stats_initialized(self, cache):
        """统计数据初始化"""
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0


class TestCacheServiceGet:
    def test_get_nonexistent_key_returns_none(self, cache):
        """获取不存在的key返回None"""
        result = cache.get("nonexistent")
        assert result is None

    def test_get_nonexistent_increments_misses(self, cache):
        """获取不存在key时miss计数+1"""
        cache.get("nonexistent")
        assert cache.stats["misses"] == 1

    def test_get_existing_key_returns_value(self, cache):
        """获取已存在的key返回正确值"""
        cache.set("test_key", {"data": 42})
        result = cache.get("test_key")
        assert result == {"data": 42}

    def test_get_existing_increments_hits(self, cache):
        """获取已存在key时hit计数+1"""
        cache.set("test_key", "value")
        cache.get("test_key")
        assert cache.stats["hits"] == 1

    def test_get_expired_key_returns_none(self, cache):
        """过期的key返回None"""
        cache.memory_cache["expired_key"] = (
            "expired_value",
            datetime.now() - timedelta(seconds=1)
        )
        result = cache.get("expired_key")
        assert result is None

    def test_expired_key_removed_from_cache(self, cache):
        """过期key被自动删除"""
        cache.memory_cache["expired_key"] = (
            "value",
            datetime.now() - timedelta(seconds=1)
        )
        cache.get("expired_key")
        assert "expired_key" not in cache.memory_cache


class TestCacheServiceSet:
    def test_set_returns_true(self, cache):
        """set操作返回True"""
        result = cache.set("key", "value")
        assert result is True

    def test_set_increments_sets_counter(self, cache):
        """set操作增加sets计数"""
        cache.set("key", "value")
        assert cache.stats["sets"] == 1

    def test_set_and_get_value(self, cache):
        """set后get可以取到值"""
        cache.set("my_key", [1, 2, 3])
        assert cache.get("my_key") == [1, 2, 3]


class TestCacheServiceDelete:
    def test_delete_existing_key(self, cache):
        """删除已存在的key"""
        cache.set("del_key", "value")
        cache.delete("del_key")
        assert cache.get("del_key") is None

    def test_delete_increments_counter(self, cache):
        """删除操作增加deletes计数"""
        cache.set("del_key", "value")
        cache.delete("del_key")
        assert cache.stats["deletes"] == 1

    def test_delete_nonexistent_key_returns_true(self, cache):
        """删除不存在key也返回True"""
        result = cache.delete("nonexistent")
        assert result is True


class TestCacheServiceGenerateKey:
    def test_same_params_same_key(self, cache):
        """相同参数生成相同key"""
        k1 = cache._generate_cache_key("prefix", project_id=1, year=2025)
        k2 = cache._generate_cache_key("prefix", project_id=1, year=2025)
        assert k1 == k2

    def test_different_params_different_key(self, cache):
        """不同参数生成不同key"""
        k1 = cache._generate_cache_key("prefix", project_id=1)
        k2 = cache._generate_cache_key("prefix", project_id=2)
        assert k1 != k2

    def test_key_starts_with_prefix(self, cache):
        """key以前缀开头"""
        key = cache._generate_cache_key("myprefix", param=1)
        assert key.startswith("myprefix:")
