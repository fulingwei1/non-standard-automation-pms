# -*- coding: utf-8 -*-
"""
CacheService 综合单元测试

测试覆盖:
- get/set/delete: 基本缓存操作
- delete_pattern: 按模式删除缓存
- clear: 清空所有缓存
- 项目相关缓存方法: get/set/invalidate project_detail/list/statistics
- get_stats/reset_stats: 缓存统计
- get_redis_info: Redis信息获取
- Redis/内存缓存降级
"""

import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestCacheServiceInit:
    """测试 CacheService 初始化"""

    def test_initializes_with_redis_client(self):
        """测试使用Redis客户端初始化"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            assert service.redis_client == mock_redis
            assert service.use_redis is True
            assert service.memory_cache == {}

    def test_initializes_without_redis(self):
        """测试不使用Redis初始化"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            assert service.redis_client is None
            assert service.use_redis is False

    def test_initializes_stats(self):
        """测试初始化统计数据"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            assert service.stats['hits'] == 0
            assert service.stats['misses'] == 0
            assert service.stats['sets'] == 0
            assert service.stats['deletes'] == 0
            assert service.stats['errors'] == 0

    def test_tries_to_get_redis_from_utils(self):
        """测试尝试从工具模块获取Redis客户端"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()

        with patch('app.services.cache_service.REDIS_AVAILABLE', True), \
             patch('app.utils.redis_client.get_redis_client', return_value=mock_redis):
            service = CacheService()

            assert service.redis_client == mock_redis
            assert service.use_redis is True


class TestGenerateCacheKey:
    """测试 _generate_cache_key 方法"""

    def test_generates_consistent_key(self):
        """测试生成一致的缓存键"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            key1 = service._generate_cache_key("test", a=1, b=2)
            key2 = service._generate_cache_key("test", a=1, b=2)

            assert key1 == key2
            assert key1.startswith("test:")

    def test_different_params_generate_different_keys(self):
        """测试不同参数生成不同键"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            key1 = service._generate_cache_key("test", a=1)
            key2 = service._generate_cache_key("test", a=2)

            assert key1 != key2

    def test_param_order_does_not_affect_key(self):
        """测试参数顺序不影响键"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            key1 = service._generate_cache_key("test", a=1, b=2)
            key2 = service._generate_cache_key("test", b=2, a=1)

            assert key1 == key2


class TestGet:
    """测试 get 方法"""

    def test_returns_none_when_key_not_exists(self):
        """测试键不存在时返回None"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.get("nonexistent")

            assert result is None
            assert service.stats['misses'] == 1

    def test_returns_value_from_memory_cache(self):
        """测试从内存缓存返回值"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["test_key"] = ({"data": 123}, None)

            result = service.get("test_key")

            assert result == {"data": 123}
            assert service.stats['hits'] == 1

    def test_returns_value_from_redis(self):
        """测试从Redis返回值"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.get.return_value = json.dumps({"data": 456})

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.get("test_key")

            assert result == {"data": 456}
            assert service.stats['hits'] == 1

    def test_returns_none_when_expired(self):
        """测试过期时返回None"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            expired_time = datetime.now() - timedelta(seconds=10)
            service.memory_cache["test_key"] = ({"data": 123}, expired_time)

            result = service.get("test_key")

            assert result is None
            assert "test_key" not in service.memory_cache
            assert service.stats['misses'] == 1

    def test_falls_back_to_memory_on_redis_error(self):
        """测试Redis错误时降级到内存缓存"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.get.side_effect = Exception("Redis error")

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)
            service.memory_cache["test_key"] = ({"data": 789}, None)

            result = service.get("test_key")

            assert result == {"data": 789}
            assert service.stats['errors'] == 1
            assert service.stats['hits'] == 1


class TestSet:
    """测试 set 方法"""

    def test_sets_value_in_memory_cache(self):
        """测试在内存缓存中设置值"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.set("test_key", {"data": 123}, expire_seconds=300)

            assert result is True
            assert "test_key" in service.memory_cache
            assert service.memory_cache["test_key"][0] == {"data": 123}
            assert service.stats['sets'] == 1

    def test_sets_value_in_redis(self):
        """测试在Redis中设置值"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.set("test_key", {"data": 456}, expire_seconds=300)

            assert result is True
            mock_redis.setex.assert_called_once()
            assert service.stats['sets'] == 1

    def test_sets_with_no_expiration(self):
        """测试设置无过期时间"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.set("test_key", {"data": 123}, expire_seconds=0)

            assert result is True
            assert service.memory_cache["test_key"][1] is None  # No expiration

    def test_falls_back_to_memory_on_redis_error(self):
        """测试Redis错误时降级到内存缓存"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.setex.side_effect = Exception("Redis error")

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.set("test_key", {"data": 789})

            assert result is True
            assert "test_key" in service.memory_cache
            assert service.stats['errors'] == 1


class TestDelete:
    """测试 delete 方法"""

    def test_deletes_from_memory_cache(self):
        """测试从内存缓存删除"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["test_key"] = ({"data": 123}, None)

            result = service.delete("test_key")

            assert result is True
            assert "test_key" not in service.memory_cache
            assert service.stats['deletes'] == 1

    def test_deletes_from_redis(self):
        """测试从Redis删除"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.delete("test_key")

            assert result is True
            mock_redis.delete.assert_called_once_with("test_key")
            assert service.stats['deletes'] == 1

    def test_returns_true_when_key_not_exists(self):
        """测试键不存在时也返回True"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.delete("nonexistent")

            assert result is True

    def test_handles_redis_error_gracefully(self):
        """测试优雅处理Redis错误"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.delete.side_effect = Exception("Redis error")

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.delete("test_key")

            assert result is True


class TestDeletePattern:
    """测试 delete_pattern 方法"""

    def test_deletes_matching_keys_from_memory(self):
        """测试从内存删除匹配的键"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["project:1"] = ({"data": 1}, None)
            service.memory_cache["project:2"] = ({"data": 2}, None)
            service.memory_cache["user:1"] = ({"data": 3}, None)

            count = service.delete_pattern("project:*")

            assert count == 2
            assert "project:1" not in service.memory_cache
            assert "project:2" not in service.memory_cache
            assert "user:1" in service.memory_cache

    def test_deletes_from_redis(self):
        """测试从Redis按模式删除"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.keys.return_value = ["project:1", "project:2"]
        mock_redis.delete.return_value = 2

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            count = service.delete_pattern("project:*")

            mock_redis.keys.assert_called_once_with("project:*")
            assert count >= 2

    def test_returns_zero_when_no_matches(self):
        """测试无匹配时返回0"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            count = service.delete_pattern("nonexistent:*")

            assert count == 0


class TestClear:
    """测试 clear 方法"""

    def test_clears_memory_cache(self):
        """测试清空内存缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["key1"] = ({"data": 1}, None)
            service.memory_cache["key2"] = ({"data": 2}, None)

            result = service.clear()

            assert result is True
            assert len(service.memory_cache) == 0

    def test_clears_redis(self):
        """测试清空Redis"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.clear()

            assert result is True
            mock_redis.flushdb.assert_called_once()

    def test_handles_redis_error_gracefully(self):
        """测试优雅处理Redis错误"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.flushdb.side_effect = Exception("Redis error")

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)
            service.memory_cache["key1"] = ({"data": 1}, None)

            result = service.clear()

            assert result is True
            assert len(service.memory_cache) == 0


class TestProjectDetailCache:
    """测试项目详情缓存方法"""

    def test_get_project_detail(self):
        """测试获取项目详情缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["project:detail:1"] = ({"id": 1, "name": "项目1"}, None)

            result = service.get_project_detail(1)

            assert result == {"id": 1, "name": "项目1"}

    def test_set_project_detail(self):
        """测试设置项目详情缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.set_project_detail(1, {"id": 1, "name": "项目1"})

            assert result is True
            assert "project:detail:1" in service.memory_cache

    def test_invalidate_project_detail(self):
        """测试使项目详情缓存失效"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["project:detail:1"] = ({"id": 1}, None)

            result = service.invalidate_project_detail(1)

            assert result is True
            assert "project:detail:1" not in service.memory_cache


class TestProjectListCache:
    """测试项目列表缓存方法"""

    def test_get_project_list(self):
        """测试获取项目列表缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            # 先设置缓存
            service.set_project_list({"items": []}, status="ACTIVE")

            # 再获取
            result = service.get_project_list(status="ACTIVE")

            assert result == {"items": []}

    def test_set_project_list(self):
        """测试设置项目列表缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.set_project_list({"items": [1, 2, 3]}, page=1, size=10)

            assert result is True
            assert len(service.memory_cache) == 1

    def test_invalidate_project_list(self):
        """测试使项目列表缓存失效"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["project:list:abc123"] = ({"items": []}, None)
            service.memory_cache["project:list:def456"] = ({"items": []}, None)

            count = service.invalidate_project_list()

            assert count == 2


class TestProjectStatisticsCache:
    """测试项目统计缓存方法"""

    def test_get_project_statistics(self):
        """测试获取项目统计缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            # 先设置
            service.set_project_statistics({"total": 100}, year=2026)

            # 再获取
            result = service.get_project_statistics(year=2026)

            assert result == {"total": 100}

    def test_set_project_statistics(self):
        """测试设置项目统计缓存"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.set_project_statistics({"total": 50}, month=1)

            assert result is True

    def test_invalidate_project_statistics(self):
        """测试使项目统计缓存失效"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["project:statistics:abc"] = ({"total": 100}, None)

            count = service.invalidate_project_statistics()

            assert count == 1

    def test_invalidate_all_project_cache(self):
        """测试使所有项目缓存失效"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["project:detail:1"] = ({"id": 1}, None)
            service.memory_cache["project:list:abc"] = ({"items": []}, None)
            service.memory_cache["project:statistics:xyz"] = ({"total": 0}, None)
            service.memory_cache["user:1"] = ({"name": "test"}, None)

            count = service.invalidate_all_project_cache()

            assert count == 3
            assert "user:1" in service.memory_cache


class TestGetStats:
    """测试 get_stats 方法"""

    def test_returns_initial_stats(self):
        """测试返回初始统计"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            stats = service.get_stats()

            assert stats['hits'] == 0
            assert stats['misses'] == 0
            assert stats['sets'] == 0
            assert stats['deletes'] == 0
            assert stats['errors'] == 0
            assert stats['total_requests'] == 0
            assert stats['hit_rate'] == 0
            assert stats['cache_type'] == 'memory'

    def test_calculates_hit_rate(self):
        """测试计算命中率"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.stats['hits'] = 80
            service.stats['misses'] = 20

            stats = service.get_stats()

            assert stats['total_requests'] == 100
            assert stats['hit_rate'] == 80.0

    def test_shows_redis_cache_type(self):
        """测试显示Redis缓存类型"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            stats = service.get_stats()

            assert stats['cache_type'] == 'redis'

    def test_shows_memory_cache_size(self):
        """测试显示内存缓存大小"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.memory_cache["key1"] = ({"data": 1}, None)
            service.memory_cache["key2"] = ({"data": 2}, None)

            stats = service.get_stats()

            assert stats['memory_cache_size'] == 2


class TestResetStats:
    """测试 reset_stats 方法"""

    def test_resets_all_stats(self):
        """测试重置所有统计"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)
            service.stats['hits'] = 100
            service.stats['misses'] = 50
            service.stats['sets'] = 30
            service.stats['deletes'] = 10
            service.stats['errors'] = 5

            service.reset_stats()

            assert service.stats['hits'] == 0
            assert service.stats['misses'] == 0
            assert service.stats['sets'] == 0
            assert service.stats['deletes'] == 0
            assert service.stats['errors'] == 0


class TestGetRedisInfo:
    """测试 get_redis_info 方法"""

    def test_returns_none_when_not_using_redis(self):
        """测试不使用Redis时返回None"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            result = service.get_redis_info()

            assert result is None

    def test_returns_redis_info(self):
        """测试返回Redis信息"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.info.return_value = {
            "connected_clients": 5,
            "used_memory_human": "1M",
            "used_memory_peak_human": "2M",
            "keyspace_hits": 1000,
            "keyspace_misses": 100,
        }

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.get_redis_info()

            assert result['connected_clients'] == 5
            assert result['used_memory_human'] == "1M"
            assert result['keyspace_hits'] == 1000
            assert result['keyspace_misses'] == 100

    def test_returns_none_on_error(self):
        """测试错误时返回None"""
        from app.services.cache_service import CacheService

        mock_redis = MagicMock()
        mock_redis.info.side_effect = Exception("Redis error")

        with patch('app.services.cache_service.REDIS_AVAILABLE', True):
            service = CacheService(redis_client=mock_redis)

            result = service.get_redis_info()

            assert result is None


class TestIntegration:
    """集成测试"""

    def test_full_cache_lifecycle(self):
        """测试完整缓存生命周期"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            # 设置缓存
            service.set("test_key", {"value": 123})

            # 获取缓存
            result = service.get("test_key")
            assert result == {"value": 123}

            # 删除缓存
            service.delete("test_key")

            # 验证已删除
            result = service.get("test_key")
            assert result is None

            # 检查统计
            stats = service.get_stats()
            assert stats['sets'] == 1
            assert stats['hits'] == 1
            assert stats['deletes'] == 1
            assert stats['misses'] == 1

    def test_project_cache_workflow(self):
        """测试项目缓存工作流"""
        from app.services.cache_service import CacheService

        with patch('app.services.cache_service.REDIS_AVAILABLE', False):
            service = CacheService(redis_client=None)

            # 设置项目详情
            service.set_project_detail(1, {"id": 1, "name": "测试项目"})

            # 获取项目详情
            detail = service.get_project_detail(1)
            assert detail['name'] == "测试项目"

            # 设置项目列表
            service.set_project_list({"items": [1, 2, 3]}, status="ACTIVE")

            # 获取项目列表
            list_cache = service.get_project_list(status="ACTIVE")
            assert list_cache['items'] == [1, 2, 3]

            # 使所有项目缓存失效
            service.invalidate_all_project_cache()

            # 验证缓存已清空
            assert service.get_project_detail(1) is None
