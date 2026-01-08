# -*- coding: utf-8 -*-
"""
缓存服务单元测试

Sprint 5.3: 性能优化 - 缓存机制测试
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.cache_service import CacheService


class TestCacheService:
    """缓存服务测试类"""
    
    def test_memory_cache_basic(self):
        """测试内存缓存基本功能"""
        cache = CacheService()
        
        # 测试设置和获取
        cache.set("test_key", {"data": "test"}, expire_seconds=60)
        value = cache.get("test_key")
        assert value == {"data": "test"}
        
        # 测试缓存命中统计
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["sets"] == 1
    
    def test_memory_cache_expiration(self):
        """测试内存缓存过期"""
        cache = CacheService()
        
        # 设置短期过期
        cache.set("expire_key", "value", expire_seconds=1)
        assert cache.get("expire_key") == "value"
        
        # 等待过期
        time.sleep(1.1)
        assert cache.get("expire_key") is None
        assert cache.get_stats()["misses"] >= 1
    
    def test_memory_cache_delete(self):
        """测试内存缓存删除"""
        cache = CacheService()
        
        cache.set("delete_key", "value")
        assert cache.get("delete_key") == "value"
        
        cache.delete("delete_key")
        assert cache.get("delete_key") is None
        assert cache.get_stats()["deletes"] == 1
    
    def test_memory_cache_delete_pattern(self):
        """测试按模式删除缓存"""
        cache = CacheService()
        
        cache.set("project:detail:1", {"id": 1})
        cache.set("project:detail:2", {"id": 2})
        cache.set("project:list:abc", {"items": []})
        cache.set("other:key", "value")
        
        deleted = cache.delete_pattern("project:*")
        assert deleted >= 2
        
        assert cache.get("project:detail:1") is None
        assert cache.get("project:detail:2") is None
        assert cache.get("project:list:abc") is None
        assert cache.get("other:key") == "value"  # 不应该被删除
    
    @pytest.mark.skipif(True, reason="需要Redis服务")
    def test_redis_cache_basic(self):
        """测试Redis缓存基本功能（需要Redis服务）"""
        import redis
        redis_client = redis.from_url("redis://localhost:6379/1", decode_responses=True)
        cache = CacheService(redis_client=redis_client)
        
        # 测试设置和获取
        cache.set("test_key", {"data": "test"}, expire_seconds=60)
        value = cache.get("test_key")
        assert value == {"data": "test"}
        
        # 清理
        cache.delete("test_key")
    
    def test_cache_stats(self):
        """测试缓存统计"""
        cache = CacheService()
        
        # 执行一些操作
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        cache.delete("key1")
        
        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1
        assert stats["deletes"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 50.0
    
    def test_cache_stats_reset(self):
        """测试缓存统计重置"""
        cache = CacheService()
        
        cache.set("key", "value")
        cache.get("key")
        
        stats_before = cache.get_stats()
        assert stats_before["hits"] > 0
        
        cache.reset_stats()
        stats_after = cache.get_stats()
        assert stats_after["hits"] == 0
        assert stats_after["misses"] == 0
    
    def test_project_cache_methods(self):
        """测试项目相关缓存方法"""
        cache = CacheService()
        
        # 测试项目详情缓存
        project_data = {"id": 1, "name": "Test Project"}
        cache.set_project_detail(1, project_data, expire_seconds=600)
        
        cached = cache.get_project_detail(1)
        assert cached == project_data
        
        # 测试缓存失效
        cache.invalidate_project_detail(1)
        assert cache.get_project_detail(1) is None
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        cache = CacheService()
        
        key1 = cache._generate_cache_key("project:list", page=1, page_size=20)
        key2 = cache._generate_cache_key("project:list", page=1, page_size=20)
        key3 = cache._generate_cache_key("project:list", page=2, page_size=20)
        
        # 相同参数应该生成相同键
        assert key1 == key2
        # 不同参数应该生成不同键
        assert key1 != key3
