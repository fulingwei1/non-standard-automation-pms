# -*- coding: utf-8 -*-
"""
Redis缓存服务单元测试

测试策略：
1. 只mock外部依赖（redis.Redis及其方法）
2. 让业务逻辑真正执行
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import json
import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch, Mock
from app.services.cache.redis_cache import (
    RedisCache,
    get_cache,
    cache_key,
    cache_result,
    CacheKeys,
    RedisCacheManager,
    CacheManager,
    REDIS_AVAILABLE,
)


class TestRedisCache(unittest.TestCase):
    """测试 RedisCache 核心类"""

    def setUp(self):
        """每个测试前重置全局缓存实例"""
        import app.services.cache.redis_cache as cache_module
        cache_module._cache_instance = None

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_init_success(self, mock_redis_class):
        """测试成功初始化"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        cache = RedisCache(
            host="localhost",
            port=6379,
            db=0,
            password="test_pass",
            decode_responses=True
        )

        self.assertEqual(cache.host, "localhost")
        self.assertEqual(cache.port, 6379)
        self.assertEqual(cache.db, 0)
        self.assertEqual(cache.password, "test_pass")
        self.assertTrue(cache.decode_responses)
        self.assertIsNotNone(cache.client)
        mock_client.ping.assert_called_once()

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_init_connection_failed(self, mock_redis_class):
        """测试连接失败"""
        mock_client = MagicMock()
        mock_client.ping.side_effect = Exception("Connection refused")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        self.assertIsNone(cache.client)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', False)
    def test_init_redis_not_available(self):
        """测试Redis未安装"""
        cache = RedisCache()
        self.assertIsNone(cache.client)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_is_available_success(self, mock_redis_class):
        """测试Redis可用检查 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        self.assertTrue(cache.is_available())

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_is_available_ping_failed(self, mock_redis_class):
        """测试Redis可用检查 - ping失败"""
        mock_client = MagicMock()
        mock_client.ping.side_effect = [True, Exception("Connection lost")]
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        self.assertFalse(cache.is_available())

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', False)
    def test_is_available_not_installed(self):
        """测试Redis未安装时is_available返回False"""
        cache = RedisCache()
        self.assertFalse(cache.is_available())

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_set_success(self, mock_redis_class):
        """测试设置缓存 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.set.return_value = True
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", {"name": "张三", "age": 30}, expire=300)

        self.assertTrue(result)
        mock_client.set.assert_called_once()
        args = mock_client.set.call_args
        self.assertEqual(args[0][0], "test_key")
        # 验证值被JSON序列化
        stored_value = json.loads(args[0][1].decode('utf-8'))
        self.assertEqual(stored_value, {"name": "张三", "age": 30})
        self.assertEqual(args[1]['ex'], 300)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_set_with_timedelta(self, mock_redis_class):
        """测试设置缓存 - 使用timedelta过期时间"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.set.return_value = True
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", "value", expire=timedelta(minutes=5))

        self.assertTrue(result)
        args = mock_client.set.call_args
        self.assertEqual(args[1]['ex'], timedelta(minutes=5))

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_set_decode_responses_true(self, mock_redis_class):
        """测试设置缓存 - decode_responses=True"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.set.return_value = True
        mock_redis_class.return_value = mock_client

        cache = RedisCache(decode_responses=True)
        result = cache.set("test_key", {"data": "测试"})

        self.assertTrue(result)
        args = mock_client.set.call_args
        # decode_responses=True时，不需要encode
        self.assertIsInstance(args[0][1], str)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_set_failed(self, mock_redis_class):
        """测试设置缓存 - 失败"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.set.side_effect = Exception("Set failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", "value")

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_set_redis_unavailable(self, mock_redis_class):
        """测试设置缓存 - Redis不可用"""
        mock_client = MagicMock()
        mock_client.ping.side_effect = [True, Exception("Connection lost")]
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.set("test_key", "value")

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_success(self, mock_redis_class):
        """测试获取缓存 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        test_data = {"name": "李四", "dept": "研发部"}
        mock_client.get.return_value = json.dumps(test_data).encode('utf-8')
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.get("test_key")

        self.assertEqual(result, test_data)
        mock_client.get.assert_called_once_with("test_key")

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_not_found(self, mock_redis_class):
        """测试获取缓存 - 不存在"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.get("nonexistent_key")

        self.assertIsNone(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_decode_responses_true(self, mock_redis_class):
        """测试获取缓存 - decode_responses=True"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        test_data = {"key": "value"}
        mock_client.get.return_value = json.dumps(test_data)  # 字符串，不是bytes
        mock_redis_class.return_value = mock_client

        cache = RedisCache(decode_responses=True)
        result = cache.get("test_key")

        self.assertEqual(result, test_data)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_failed(self, mock_redis_class):
        """测试获取缓存 - 异常"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.side_effect = Exception("Get failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.get("test_key")

        self.assertIsNone(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_invalid_json(self, mock_redis_class):
        """测试获取缓存 - JSON解析失败"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = b"invalid json"
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.get("test_key")

        self.assertIsNone(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_delete_success(self, mock_redis_class):
        """测试删除缓存 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.return_value = 1
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.delete("test_key")

        self.assertTrue(result)
        mock_client.delete.assert_called_once_with("test_key")

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_delete_not_exist(self, mock_redis_class):
        """测试删除缓存 - 键不存在"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.return_value = 0
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.delete("nonexistent_key")

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_delete_failed(self, mock_redis_class):
        """测试删除缓存 - 异常"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.delete.side_effect = Exception("Delete failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.delete("test_key")

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_exists_true(self, mock_redis_class):
        """测试检查缓存存在 - 存在"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 1
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.exists("test_key")

        self.assertTrue(result)
        mock_client.exists.assert_called_once_with("test_key")

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_exists_false(self, mock_redis_class):
        """测试检查缓存存在 - 不存在"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.exists.return_value = 0
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.exists("nonexistent_key")

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_exists_failed(self, mock_redis_class):
        """测试检查缓存存在 - 异常"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.exists.side_effect = Exception("Exists failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.exists("test_key")

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_pattern_success(self, mock_redis_class):
        """测试按模式清除缓存 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = [b"user:1", b"user:2", b"user:3"]
        mock_client.delete.return_value = 3
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.clear_pattern("user:*")

        self.assertEqual(result, 3)
        mock_client.keys.assert_called_once_with("user:*")
        mock_client.delete.assert_called_once()

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_pattern_no_keys(self, mock_redis_class):
        """测试按模式清除缓存 - 无匹配键"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.clear_pattern("nonexistent:*")

        self.assertEqual(result, 0)
        mock_client.delete.assert_not_called()

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_pattern_failed(self, mock_redis_class):
        """测试按模式清除缓存 - 异常"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.side_effect = Exception("Keys failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.clear_pattern("user:*")

        self.assertEqual(result, 0)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_increment_success(self, mock_redis_class):
        """测试递增 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 5
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.increment("counter", amount=2)

        self.assertEqual(result, 5)
        mock_client.incr.assert_called_once_with("counter", 2)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_increment_default_amount(self, mock_redis_class):
        """测试递增 - 默认递增量"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.incr.return_value = 1
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.increment("counter")

        self.assertEqual(result, 1)
        mock_client.incr.assert_called_once_with("counter", 1)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_increment_failed(self, mock_redis_class):
        """测试递增 - 异常"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.incr.side_effect = Exception("Incr failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.increment("counter")

        self.assertIsNone(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_expire_success(self, mock_redis_class):
        """测试设置过期时间 - 成功"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.expire.return_value = 1
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.expire("test_key", 300)

        self.assertTrue(result)
        mock_client.expire.assert_called_once_with("test_key", 300)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_expire_key_not_exist(self, mock_redis_class):
        """测试设置过期时间 - 键不存在"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.expire.return_value = 0
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.expire("nonexistent_key", 300)

        self.assertFalse(result)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_expire_failed(self, mock_redis_class):
        """测试设置过期时间 - 异常"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.expire.side_effect = Exception("Expire failed")
        mock_redis_class.return_value = mock_client

        cache = RedisCache()
        result = cache.expire("test_key", 300)

        self.assertFalse(result)


class TestGlobalCacheInstance(unittest.TestCase):
    """测试全局缓存实例"""

    def setUp(self):
        """每个测试前重置全局缓存实例"""
        import app.services.cache.redis_cache as cache_module
        cache_module._cache_instance = None

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_cache_singleton(self, mock_redis_class):
        """测试get_cache返回单例"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        cache1 = get_cache()
        cache2 = get_cache()

        self.assertIs(cache1, cache2)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_get_cache_creates_instance(self, mock_redis_class):
        """测试get_cache创建实例"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        cache = get_cache()

        self.assertIsInstance(cache, RedisCache)


class TestCacheKey(unittest.TestCase):
    """测试cache_key函数"""

    def test_cache_key_single_part(self):
        """测试单个部分"""
        result = cache_key("user")
        self.assertEqual(result, "user")

    def test_cache_key_multiple_parts(self):
        """测试多个部分"""
        result = cache_key("user", 123, "profile")
        self.assertEqual(result, "user:123:profile")

    def test_cache_key_mixed_types(self):
        """测试混合类型"""
        result = cache_key("project", 456, "stats", True)
        self.assertEqual(result, "project:456:stats:True")

    def test_cache_key_empty(self):
        """测试空参数"""
        result = cache_key()
        self.assertEqual(result, "")


class TestCacheKeys(unittest.TestCase):
    """测试CacheKeys常量"""

    def test_cache_keys_constants(self):
        """测试缓存键常量"""
        self.assertEqual(CacheKeys.PROJECT, "project")
        self.assertEqual(CacheKeys.USER, "user")
        self.assertEqual(CacheKeys.ALERT, "alert")
        self.assertEqual(CacheKeys.CONFIG, "config")
        self.assertEqual(CacheKeys.DASHBOARD, "dashboard")


class TestCacheResultDecorator(unittest.TestCase):
    """测试cache_result装饰器"""

    def setUp(self):
        """每个测试前重置全局缓存实例"""
        import app.services.cache.redis_cache as cache_module
        cache_module._cache_instance = None

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_cache_result_decorator_cache_hit(self, mock_redis_class):
        """测试装饰器 - 缓存命中"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        
        # 第一次get返回None（未缓存），第二次返回缓存值
        cached_value = json.dumps({"result": 3}).encode('utf-8')
        mock_client.get.side_effect = [None, cached_value]
        mock_client.set.return_value = True
        mock_redis_class.return_value = mock_client

        call_count = 0

        @cache_result("test_func", expire=300)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return {"result": x + y}

        result1 = test_function(1, 2)
        result2 = test_function(1, 2)

        # 第一次调用执行函数，第二次从缓存读取
        self.assertEqual(result1, {"result": 3})
        self.assertEqual(result2, {"result": 3})
        # 函数只执行一次（第一次调用时）
        self.assertEqual(call_count, 1)
        # 验证set被调用一次（第一次调用后缓存结果）
        mock_client.set.assert_called_once()

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_cache_result_decorator_cache_miss(self, mock_redis_class):
        """测试装饰器 - 缓存未命中"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_redis_class.return_value = mock_client

        call_count = 0

        @cache_result("test_func", expire=300)
        def test_function(x, y):
            nonlocal call_count
            call_count += 1
            return {"result": x + y}

        result = test_function(1, 2)

        self.assertEqual(result, {"result": 3})
        self.assertEqual(call_count, 1)
        # 验证缓存被设置
        mock_client.set.assert_called_once()


class TestRedisCacheManager(unittest.TestCase):
    """测试RedisCacheManager缓存管理工具"""

    def setUp(self):
        """每个测试前重置全局缓存实例"""
        import app.services.cache.redis_cache as cache_module
        cache_module._cache_instance = None

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_project_cache_specific(self, mock_redis_class):
        """测试清除特定项目缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_project_cache(project_id=123)

        # 验证调用了3次keys（3个模式）
        self.assertEqual(mock_client.keys.call_count, 3)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_project_cache_all(self, mock_redis_class):
        """测试清除所有项目缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_project_cache()

        # 验证调用了4次keys（4个模式）
        self.assertEqual(mock_client.keys.call_count, 4)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_user_cache_specific(self, mock_redis_class):
        """测试清除特定用户缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_user_cache(user_id=456)

        self.assertEqual(mock_client.keys.call_count, 3)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_user_cache_all(self, mock_redis_class):
        """测试清除所有用户缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_user_cache()

        self.assertEqual(mock_client.keys.call_count, 3)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_alert_cache(self, mock_redis_class):
        """测试清除告警缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_alert_cache()

        self.assertEqual(mock_client.keys.call_count, 2)

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_search_cache(self, mock_redis_class):
        """测试清除搜索缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_search_cache()

        mock_client.keys.assert_called_once()

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_dashboard_cache(self, mock_redis_class):
        """测试清除仪表板缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.keys.return_value = []
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_dashboard_cache()

        mock_client.keys.assert_called_once()

    @patch('app.services.cache.redis_cache.REDIS_AVAILABLE', True)
    @patch('app.services.cache.redis_cache.redis.Redis')
    def test_clear_all_cache(self, mock_redis_class):
        """测试清除所有缓存"""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_client.flushdb.return_value = True
        mock_redis_class.return_value = mock_client

        RedisCacheManager.clear_all_cache()

        mock_client.flushdb.assert_called_once()


class TestBackwardCompatibility(unittest.TestCase):
    """测试向后兼容性"""

    def test_cache_manager_alias(self):
        """测试CacheManager别名"""
        self.assertIs(CacheManager, RedisCacheManager)


if __name__ == "__main__":
    unittest.main()
