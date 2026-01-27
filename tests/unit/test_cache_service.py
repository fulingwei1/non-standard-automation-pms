# -*- coding: utf-8 -*-
"""
缓存服务单元测试

Sprint 5.3: 性能优化 - 缓存机制测试
"""

import time
from unittest.mock import Mock, patch

import pytest

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


@pytest.mark.unit
class TestCacheServiceRedis:
    """Redis 缓存功能测试（使用 Mock）"""

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_get_hit(self):
        """测试 Redis 缓存命中"""
        import json
        mock_redis = Mock()
        mock_redis.get.return_value = json.dumps({"data": "redis_value"})

        cache = CacheService(redis_client=mock_redis)

        result = cache.get("test_key")

        assert result == {"data": "redis_value"}
        assert cache.stats["hits"] == 1
        mock_redis.get.assert_called_once_with("test_key")

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_get_miss(self):
        """测试 Redis 缓存未命中"""
        mock_redis = Mock()
        mock_redis.get.return_value = None

        cache = CacheService(redis_client=mock_redis)

        result = cache.get("nonexistent")

        assert result is None
        # Redis miss + memory cache miss = 2
        assert cache.stats["misses"] == 2

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_get_error_fallback(self):
        """测试 Redis 获取错误时降级到内存"""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis connection error")

        cache = CacheService(redis_client=mock_redis)
        # 在内存缓存中放入值
        cache.memory_cache["test_key"] = ({"data": "memory_value"}, None)

        result = cache.get("test_key")

        assert result == {"data": "memory_value"}
        assert cache.stats["errors"] == 1

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_set_success(self):
        """测试 Redis 设置成功"""
        mock_redis = Mock()

        cache = CacheService(redis_client=mock_redis)
        result = cache.set("test_key", {"data": "value"}, expire_seconds=300)

        assert result is True
        mock_redis.setex.assert_called_once()
        assert cache.stats["sets"] == 1

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_set_error_fallback(self):
        """测试 Redis 设置错误时降级到内存"""
        mock_redis = Mock()
        mock_redis.setex.side_effect = Exception("Redis connection error")

        cache = CacheService(redis_client=mock_redis)
        result = cache.set("test_key", {"data": "value"})

        assert result is True
        assert "test_key" in cache.memory_cache
        assert cache.stats["errors"] == 1

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_delete(self):
        """测试 Redis 删除"""
        mock_redis = Mock()

        cache = CacheService(redis_client=mock_redis)
        cache.delete("test_key")

        mock_redis.delete.assert_called_once_with("test_key")
        assert cache.stats["deletes"] == 1

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_delete_error(self):
        """测试 Redis 删除错误"""
        mock_redis = Mock()
        mock_redis.delete.side_effect = Exception("Redis error")

        cache = CacheService(redis_client=mock_redis)
        result = cache.delete("test_key")

        # 删除总是返回 True
        assert result is True

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_delete_pattern(self):
        """测试 Redis 按模式删除"""
        mock_redis = Mock()
        mock_redis.keys.return_value = ["project:1", "project:2"]
        mock_redis.delete.return_value = 2

        cache = CacheService(redis_client=mock_redis)
        deleted = cache.delete_pattern("project:*")

        mock_redis.keys.assert_called_once_with("project:*")
        assert deleted >= 2

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_delete_pattern_error(self):
        """测试 Redis 按模式删除错误"""
        mock_redis = Mock()
        mock_redis.keys.side_effect = Exception("Redis error")

        cache = CacheService(redis_client=mock_redis)
        # 设置内存缓存
        cache.memory_cache["project:1"] = ("v1", None)

        deleted = cache.delete_pattern("project:*")

        # 应该仍然删除内存缓存
        assert deleted >= 1

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_clear(self):
        """测试 Redis 清空"""
        mock_redis = Mock()

        cache = CacheService(redis_client=mock_redis)
        cache.memory_cache["key"] = ("value", None)

        result = cache.clear()

        assert result is True
        mock_redis.flushdb.assert_called_once()
        assert len(cache.memory_cache) == 0

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_clear_error(self):
        """测试 Redis 清空错误"""
        mock_redis = Mock()
        mock_redis.flushdb.side_effect = Exception("Redis error")

        cache = CacheService(redis_client=mock_redis)
        cache.memory_cache["key"] = ("value", None)

        result = cache.clear()

        # 应该仍然清空内存缓存
        assert result is True
        assert len(cache.memory_cache) == 0


@pytest.mark.unit
class TestProjectCacheMethodsExtended:
    """扩展的项目缓存方法测试"""

    def test_project_list_cache(self):
        """测试项目列表缓存"""
        cache = CacheService()

        list_data = {"items": [{"id": 1}, {"id": 2}], "total": 2}
        cache.set_project_list(list_data, expire_seconds=300, page=1, status="active")

        cached = cache.get_project_list(page=1, status="active")
        assert cached == list_data

        # 不同参数应该获取不到
        different = cache.get_project_list(page=2, status="active")
        assert different is None

    def test_project_statistics_cache(self):
        """测试项目统计缓存"""
        cache = CacheService()

        stats_data = {"total": 100, "active": 80, "completed": 20}
        cache.set_project_statistics(stats_data, expire_seconds=600, year=2024)

        cached = cache.get_project_statistics(year=2024)
        assert cached == stats_data

    def test_invalidate_project_list(self):
        """测试使项目列表缓存失效"""
        cache = CacheService()

        cache.set_project_list({"items": []}, page=1)
        cache.set_project_list({"items": []}, page=2)

        deleted = cache.invalidate_project_list()
        assert deleted >= 2

    def test_invalidate_project_statistics(self):
        """测试使项目统计缓存失效"""
        cache = CacheService()

        cache.set_project_statistics({"total": 10}, year=2023)
        cache.set_project_statistics({"total": 20}, year=2024)

        deleted = cache.invalidate_project_statistics()
        assert deleted >= 2

    def test_invalidate_all_project_cache(self):
        """测试使所有项目缓存失效"""
        cache = CacheService()

        cache.set_project_detail(1, {"id": 1})
        cache.set_project_list({"items": []}, page=1)
        cache.set_project_statistics({"total": 10})

        deleted = cache.invalidate_all_project_cache()
        assert deleted >= 3

        # 确认全部删除
        assert cache.get_project_detail(1) is None


@pytest.mark.unit
class TestRedisInfo:
    """Redis 信息测试"""

    def test_get_redis_info_not_using_redis(self):
        """测试不使用 Redis 时获取信息"""
        cache = CacheService()

        info = cache.get_redis_info()

        assert info is None

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_get_redis_info_success(self):
        """测试成功获取 Redis 信息"""
        mock_redis = Mock()
        mock_redis.info.return_value = {
        "connected_clients": 5,
        "used_memory_human": "1.5M",
        "used_memory_peak_human": "2M",
        "keyspace_hits": 100,
        "keyspace_misses": 10,
        "db0": {"keys": "50"}
        }

        cache = CacheService(redis_client=mock_redis)
        info = cache.get_redis_info()

        assert info is not None
        assert info["connected_clients"] == 5
        assert info["used_memory_human"] == "1.5M"
        assert info["keyspace_hits"] == 100

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_get_redis_info_error(self):
        """测试获取 Redis 信息错误"""
        mock_redis = Mock()
        mock_redis.info.side_effect = Exception("Redis error")

        cache = CacheService(redis_client=mock_redis)
        info = cache.get_redis_info()

        assert info is None

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_get_redis_info_no_db0(self):
        """测试 Redis 信息中没有 db0"""
        mock_redis = Mock()
        mock_redis.info.return_value = {
        "connected_clients": 1,
        "used_memory_human": "1M",
        "used_memory_peak_human": "1M",
        "keyspace_hits": 0,
        "keyspace_misses": 0
            # 没有 db0
        }

        cache = CacheService(redis_client=mock_redis)
        info = cache.get_redis_info()

        assert info is not None
        assert info["total_keys"] == 0


@pytest.mark.unit
class TestCacheServiceInit:
    """缓存服务初始化测试"""

    @patch('app.services.cache_service.REDIS_AVAILABLE', False)
    def test_init_redis_not_available(self):
        """测试 Redis 不可用时的初始化"""
        mock_redis = Mock()

        cache = CacheService(redis_client=mock_redis)

        # 即使传入了 redis_client，use_redis 也应该是 False
        assert cache.use_redis is False

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    @patch('app.utils.redis_client.get_redis_client')
    def test_init_get_redis_from_utils(self, mock_get_client):
        """测试从工具模块获取 Redis 客户端"""
        mock_redis = Mock()
        mock_get_client.return_value = mock_redis

        cache = CacheService(redis_client=None)

        mock_get_client.assert_called_once()
        assert cache.redis_client is mock_redis

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    @patch('app.utils.redis_client.get_redis_client')
    def test_init_get_redis_from_utils_fails(self, mock_get_client):
        """测试从工具模块获取 Redis 客户端失败"""
        mock_get_client.side_effect = Exception("Connection failed")

        cache = CacheService(redis_client=None)

        assert cache.redis_client is None
        assert cache.use_redis is False


@pytest.mark.unit
class TestCacheServiceIntegration:
    """集成测试"""

    def test_full_workflow(self):
        """测试完整工作流程"""
        cache = CacheService()

        # 1. 设置项目详情
        project_data = {"id": 1, "name": "Test Project", "status": "active"}
        cache.set_project_detail(1, project_data)

        # 2. 设置项目列表
        list_data = {"items": [project_data], "total": 1}
        cache.set_project_list(list_data, page=1, limit=10)

        # 3. 设置统计
        stats_data = {"total": 1, "active": 1, "completed": 0}
        cache.set_project_statistics(stats_data, year=2024)

        # 4. 获取并验证
        assert cache.get_project_detail(1) == project_data
        assert cache.get_project_list(page=1, limit=10) == list_data
        assert cache.get_project_statistics(year=2024) == stats_data

        # 5. 检查统计
        cache_stats = cache.get_stats()
        assert cache_stats["sets"] == 3
        assert cache_stats["hits"] == 3

        # 6. 使所有项目缓存失效
        cache.invalidate_all_project_cache()

        # 7. 确认已清除
        assert cache.get_project_detail(1) is None
        assert cache.get_project_list(page=1, limit=10) is None

    @patch('app.services.cache_service.REDIS_AVAILABLE', True)
    def test_redis_fallback_workflow(self):
        """测试 Redis 降级工作流程"""
        mock_redis = Mock()
        mock_redis.get.side_effect = Exception("Redis down")
        mock_redis.setex.side_effect = Exception("Redis down")

        cache = CacheService(redis_client=mock_redis)

        # 设置应该降级到内存
        result = cache.set("key", {"value": "test"})
        assert result is True
        assert "key" in cache.memory_cache

        # 获取应该降级到内存
        cached = cache.get("key")
        assert cached == {"value": "test"}

        # 统计应该记录错误
        stats = cache.get_stats()
        assert stats["errors"] >= 1
