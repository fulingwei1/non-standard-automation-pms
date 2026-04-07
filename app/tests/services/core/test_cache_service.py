# -*- coding: utf-8 -*-
"""
缓存服务测试
"""
from unittest.mock import MagicMock
from datetime import datetime, timedelta


class TestCacheService:
    """测试缓存服务"""

    def test_cache_service_initialization_with_redis(self):
        """测试Redis客户端初始化"""
        mock_redis = MagicMock()
        
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=mock_redis)
        
        assert cache.redis_client is mock_redis
        assert cache.use_redis is True

    def test_cache_service_initialization_without_redis(self):
        """测试无Redis客户端时使用内存缓存"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        assert cache.redis_client is None
        assert cache.use_redis is False
        assert isinstance(cache.memory_cache, dict)

    def test_generate_cache_key(self):
        """测试缓存键生成"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        key = cache._generate_cache_key("user", id=123, name="test")
        
        assert key.startswith("user:")
        assert len(key) > 10

    def test_generate_cache_key_deterministic(self):
        """测试相同参数生成相同缓存键"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        key1 = cache._generate_cache_key("user", id=123, name="test")
        key2 = cache._generate_cache_key("user", name="test", id=123)
        
        assert key1 == key2

    def test_cache_set_memory(self):
        """测试内存缓存设置"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        cache.set("test_key", "test_value", expire_seconds=300)
        
        assert "test_key" in cache.memory_cache

    def test_cache_get_memory_hit(self):
        """测试内存缓存命中"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        cache.set("test_key", "test_value", expire_seconds=300)
        result = cache.get("test_key")
        
        assert result == "test_value"
        assert cache.stats["hits"] == 1

    def test_cache_get_memory_miss(self):
        """测试内存缓存未命中"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        result = cache.get("nonexistent_key")
        
        assert result is None
        assert cache.stats["misses"] == 1

    def test_cache_delete(self):
        """测试缓存删除"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        cache.set("test_key", "test_value", expire_seconds=300)
        cache.delete("test_key")
        
        assert "test_key" not in cache.memory_cache

    def test_cache_clear(self):
        """测试缓存清空"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        cache.set("key1", "value1", expire_seconds=300)
        cache.set("key2", "value2", expire_seconds=300)
        cache.clear()
        
        assert len(cache.memory_cache) == 0

    def test_cache_stats_initialization(self):
        """测试缓存统计初始化"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        assert cache.stats["hits"] == 0
        assert cache.stats["misses"] == 0
        assert cache.stats["sets"] == 0
        assert cache.stats["deletes"] == 0
        assert cache.stats["errors"] == 0

    def test_cache_ttl_expiration(self):
        """测试缓存过期"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        # 手动设置一个已过期的缓存
        past_time = datetime.now() - timedelta(seconds=1)
        cache.memory_cache["expire_key"] = ("expire_value", past_time)
        
        # 获取应该返回None（已过期）
        result = cache.get("expire_key")
        
        assert result is None

    def test_cache_with_redis_set(self):
        """测试Redis缓存设置"""
        mock_redis = MagicMock()
        mock_redis.setex = MagicMock(return_value=True)
        
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=mock_redis)
        cache.set("redis_key", "redis_value", expire_seconds=300)
        
        mock_redis.setex.assert_called_once()

    def test_cache_with_redis_get(self):
        """测试Redis缓存获取"""
        mock_redis = MagicMock()
        mock_redis.get = MagicMock(return_value='{"value": "cached"}')
        
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=mock_redis)
        result = cache.get("redis_key")
        
        assert result == {"value": "cached"}
        mock_redis.get.assert_called_once()

    def test_cache_with_redis_delete(self):
        """测试Redis缓存删除"""
        mock_redis = MagicMock()
        mock_redis.delete = MagicMock(return_value=1)
        
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=mock_redis)
        cache.delete("redis_key")
        
        mock_redis.delete.assert_called_once()

    def test_delete_pattern(self):
        """测试按模式删除"""
        from app.services.cache_service import CacheService
        
        cache = CacheService(redis_client=None)
        
        cache.set("project:1", "value1", expire_seconds=300)
        cache.set("project:2", "value2", expire_seconds=300)
        cache.set("user:1", "value3", expire_seconds=300)
        
        deleted_count = cache.delete_pattern("project:*")
        
        assert deleted_count == 2
        assert "project:1" not in cache.memory_cache
        assert "project:2" not in cache.memory_cache
        assert "user:1" in cache.memory_cache