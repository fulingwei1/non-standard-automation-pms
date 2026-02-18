# -*- coding: utf-8 -*-
"""第二十一批：缓存服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

pytest.importorskip("app.services.cache_service")


@pytest.fixture
def cache_no_redis():
    """无Redis的缓存服务"""
    with patch("app.services.cache_service.REDIS_AVAILABLE", False), \
         patch("app.utils.redis_client.get_redis_client", side_effect=Exception("no redis"),
               create=True):
        from app.services.cache_service import CacheService
        return CacheService(redis_client=None)


@pytest.fixture
def cache_with_mock_redis():
    """带 mock Redis 的缓存服务"""
    mock_redis = MagicMock()
    with patch("app.services.cache_service.REDIS_AVAILABLE", True):
        from app.services.cache_service import CacheService
        svc = CacheService(redis_client=mock_redis)
    svc.redis_client = mock_redis
    svc.use_redis = True
    return svc, mock_redis


class TestCacheServiceInit:
    def test_init_without_redis(self, cache_no_redis):
        assert cache_no_redis.use_redis is False
        assert isinstance(cache_no_redis.memory_cache, dict)

    def test_stats_initialized(self, cache_no_redis):
        assert cache_no_redis.stats["hits"] == 0
        assert cache_no_redis.stats["misses"] == 0


class TestMemoryCacheSetAndGet:
    def test_set_and_get_value(self, cache_no_redis):
        cache_no_redis.set("key1", {"data": "value"}, expire_seconds=60)
        result = cache_no_redis.get("key1")
        assert result == {"data": "value"}

    def test_miss_returns_none(self, cache_no_redis):
        result = cache_no_redis.get("nonexistent_key")
        assert result is None

    def test_expired_key_returns_none(self, cache_no_redis):
        cache_no_redis.memory_cache["expired_key"] = (
            "old_value",
            datetime.now() - timedelta(seconds=1)
        )
        result = cache_no_redis.get("expired_key")
        assert result is None
        assert "expired_key" not in cache_no_redis.memory_cache

    def test_stats_update_on_hit(self, cache_no_redis):
        cache_no_redis.set("mykey", 42)
        cache_no_redis.get("mykey")
        assert cache_no_redis.stats["hits"] == 1

    def test_stats_update_on_miss(self, cache_no_redis):
        cache_no_redis.get("absent")
        assert cache_no_redis.stats["misses"] == 1


class TestMemoryCacheDelete:
    def test_delete_existing_key(self, cache_no_redis):
        cache_no_redis.set("del_key", "val")
        cache_no_redis.delete("del_key")
        assert cache_no_redis.get("del_key") is None
        assert cache_no_redis.stats["deletes"] == 1

    def test_delete_nonexistent_key(self, cache_no_redis):
        result = cache_no_redis.delete("not_there")
        assert result is True  # Always returns True


class TestGenerateCacheKey:
    def test_deterministic_key(self, cache_no_redis):
        key1 = cache_no_redis._generate_cache_key("proj", project_id=1, stage="S7")
        key2 = cache_no_redis._generate_cache_key("proj", stage="S7", project_id=1)
        assert key1 == key2

    def test_different_params_different_key(self, cache_no_redis):
        key1 = cache_no_redis._generate_cache_key("proj", project_id=1)
        key2 = cache_no_redis._generate_cache_key("proj", project_id=2)
        assert key1 != key2


class TestDeletePattern:
    def test_delete_pattern_in_memory(self, cache_no_redis):
        cache_no_redis.set("project:1:data", "val1")
        cache_no_redis.set("project:2:data", "val2")
        cache_no_redis.set("other:1:data", "val3")
        deleted = cache_no_redis.delete_pattern("project:*")
        assert deleted >= 2
