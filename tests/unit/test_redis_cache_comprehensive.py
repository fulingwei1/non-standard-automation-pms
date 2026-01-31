# -*- coding: utf-8 -*-
"""
RedisCache 综合单元测试

测试覆盖:
- __init__: 初始化缓存
- _connect: 建立连接
- is_available: 检查可用性
- set: 设置缓存
- get: 获取缓存
- delete: 删除缓存
- exists: 检查键是否存在
- expire: 设置过期时间
- ttl: 获取剩余时间
- keys: 获取匹配的键
- flush: 清空缓存
"""

from unittest.mock import MagicMock, patch
from datetime import timedelta
import json

import pytest


class TestRedisCacheInit:
    """测试 RedisCache 初始化"""

    def test_initializes_with_defaults(self):
        """测试使用默认参数初始化"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', False):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache()

            assert cache.host == "localhost"
            assert cache.port == 6379
            assert cache.db == 0
            assert cache.password is None
            assert cache.client is None

    def test_initializes_with_custom_params(self):
        """测试使用自定义参数初始化"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', False):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache(
                host="redis.example.com",
                port=6380,
                db=1,
                password="secret"
            )

            assert cache.host == "redis.example.com"
            assert cache.port == 6380
            assert cache.db == 1
            assert cache.password == "secret"

    def test_connects_when_redis_available(self):
        """测试 Redis 可用时建立连接"""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            with patch('app.services.cache.redis_cache.redis.Redis', return_value=mock_redis):
                from app.services.cache.redis_cache import RedisCache

                cache = RedisCache()

                assert cache.client is not None


class TestIsAvailable:
    """测试 is_available 方法"""

    def test_returns_false_when_redis_not_available(self):
        """测试 Redis 不可用时返回 False"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', False):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache()

            result = cache.is_available()

            assert result is False

    def test_returns_false_when_no_client(self):
        """测试没有客户端时返回 False"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = None

            result = cache.is_available()

            assert result is False

    def test_returns_true_when_ping_succeeds(self):
        """测试 ping 成功时返回 True"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.is_available()

            assert result is True

    def test_returns_false_when_ping_fails(self):
        """测试 ping 失败时返回 False"""
        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Connection failed")

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.is_available()

            assert result is False


class TestSet:
    """测试 set 方法"""

    def test_sets_value_successfully(self):
        """测试成功设置值"""
        mock_client = MagicMock()
        mock_client.set.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.set("key", "value")

            assert result is True
            mock_client.set.assert_called_once()

    def test_sets_value_with_expire(self):
        """测试设置带过期时间的值"""
        mock_client = MagicMock()
        mock_client.set.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.set("key", "value", expire=3600)

            assert result is True

    def test_sets_value_with_timedelta_expire(self):
        """测试使用 timedelta 设置过期时间"""
        mock_client = MagicMock()
        mock_client.set.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.set("key", "value", expire=timedelta(hours=1))

            assert result is True

    def test_returns_false_when_no_client(self):
        """测试没有客户端时返回 False"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = None

            result = cache.set("key", "value")

            assert result is False

    def test_handles_exception(self):
        """测试处理异常"""
        mock_client = MagicMock()
        mock_client.set.side_effect = Exception("Redis error")

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.set("key", "value")

            assert result is False


class TestGet:
    """测试 get 方法"""

    def test_gets_value_successfully(self):
        """测试成功获取值"""
        mock_client = MagicMock()
        mock_client.get.return_value = b'"test_value"'

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.get("key")

            assert result == "test_value"

    def test_returns_none_for_missing_key(self):
        """测试键不存在时返回 None"""
        mock_client = MagicMock()
        mock_client.get.return_value = None

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.get("nonexistent")

            assert result is None

    def test_returns_default_for_missing_key(self):
        """测试键不存在时返回默认值"""
        mock_client = MagicMock()
        mock_client.get.return_value = None

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.get("nonexistent", default="default_value")

            assert result == "default_value"

    def test_returns_none_when_no_client(self):
        """测试没有客户端时返回 None"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = None

            result = cache.get("key")

            assert result is None


class TestDelete:
    """测试 delete 方法"""

    def test_deletes_key_successfully(self):
        """测试成功删除键"""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.delete("key")

            assert result is True

    def test_returns_false_for_missing_key(self):
        """测试键不存在时返回 False"""
        mock_client = MagicMock()
        mock_client.delete.return_value = 0

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.delete("nonexistent")

            assert result is False

    def test_returns_false_when_no_client(self):
        """测试没有客户端时返回 False"""
        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = None

            result = cache.delete("key")

            assert result is False


class TestExists:
    """测试 exists 方法"""

    def test_returns_true_for_existing_key(self):
        """测试键存在时返回 True"""
        mock_client = MagicMock()
        mock_client.exists.return_value = 1

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.exists("key")

            assert result is True

    def test_returns_false_for_missing_key(self):
        """测试键不存在时返回 False"""
        mock_client = MagicMock()
        mock_client.exists.return_value = 0

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.exists("nonexistent")

            assert result is False


class TestExpire:
    """测试 expire 方法"""

    def test_sets_expire_successfully(self):
        """测试成功设置过期时间"""
        mock_client = MagicMock()
        mock_client.expire.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.expire("key", 3600)

            assert result is True
            mock_client.expire.assert_called_once_with("key", 3600)

    def test_handles_timedelta(self):
        """测试处理 timedelta"""
        mock_client = MagicMock()
        mock_client.expire.return_value = True

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.expire("key", timedelta(hours=1))

            assert result is True


class TestTTL:
    """测试 ttl 方法"""

    def test_returns_ttl(self):
        """测试返回剩余时间"""
        mock_client = MagicMock()
        mock_client.ttl.return_value = 3600

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.ttl("key")

            assert result == 3600

    def test_returns_negative_for_no_expire(self):
        """测试无过期时间返回 -1"""
        mock_client = MagicMock()
        mock_client.ttl.return_value = -1

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.ttl("key")

            assert result == -1


class TestKeys:
    """测试 keys 方法"""

    def test_returns_matching_keys(self):
        """测试返回匹配的键"""
        mock_client = MagicMock()
        mock_client.keys.return_value = [b"user:1", b"user:2", b"user:3"]

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.keys("user:*")

            assert len(result) == 3

    def test_returns_empty_list_for_no_matches(self):
        """测试无匹配时返回空列表"""
        mock_client = MagicMock()
        mock_client.keys.return_value = []

        with patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True):
            from app.services.cache.redis_cache import RedisCache

            cache = RedisCache.__new__(RedisCache)
            cache.client = mock_client

            result = cache.keys("nonexistent:*")

            assert result == []
