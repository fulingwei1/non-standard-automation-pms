# -*- coding: utf-8 -*-
"""第二十四批 - cache_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

pytest.importorskip("app.services.cache_service")

from app.services.cache_service import CacheService


@pytest.fixture
def cache_no_redis():
    """无 Redis 的纯内存缓存"""
    with patch("app.services.cache_service.REDIS_AVAILABLE", False):
        with patch("app.services.cache_service.get_redis_client", side_effect=Exception("no redis"), create=True):
            svc = CacheService(redis_client=None)
    return svc


class TestCacheServiceInit:
    def test_init_without_redis(self, cache_no_redis):
        assert cache_no_redis.use_redis is False
        assert isinstance(cache_no_redis.memory_cache, dict)

    def test_init_stats_zero(self, cache_no_redis):
        stats = cache_no_redis.stats
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    def test_init_with_redis_client(self):
        redis_client = MagicMock()
        with patch("app.services.cache_service.REDIS_AVAILABLE", True):
            svc = CacheService(redis_client=redis_client)
        assert svc.use_redis is True


class TestGenerateCacheKey:
    def test_same_params_same_key(self, cache_no_redis):
        key1 = cache_no_redis._generate_cache_key("prefix", user_id=1, scope="all")
        key2 = cache_no_redis._generate_cache_key("prefix", user_id=1, scope="all")
        assert key1 == key2

    def test_different_params_different_key(self, cache_no_redis):
        key1 = cache_no_redis._generate_cache_key("prefix", user_id=1)
        key2 = cache_no_redis._generate_cache_key("prefix", user_id=2)
        assert key1 != key2

    def test_key_contains_prefix(self, cache_no_redis):
        key = cache_no_redis._generate_cache_key("myprefix", x=1)
        assert "myprefix" in key


class TestMemoryCache:
    def test_set_and_get_value(self, cache_no_redis):
        """直接操作内存缓存验证存取"""
        svc = cache_no_redis
        expire_at = datetime.now() + timedelta(seconds=60)
        svc.memory_cache["test_key"] = ({"data": 42}, expire_at)
        val, exp = svc.memory_cache["test_key"]
        assert val == {"data": 42}

    def test_memory_cache_initially_empty(self, cache_no_redis):
        assert len(cache_no_redis.memory_cache) == 0

    def test_stats_tracking(self, cache_no_redis):
        # Stats dict should have all expected keys
        for key in ("hits", "misses", "sets", "deletes", "errors"):
            assert key in cache_no_redis.stats
