# -*- coding: utf-8 -*-
"""RedisCache 单元测试"""

import unittest
from unittest.mock import MagicMock, patch

# Ensure redis module is available as mock if not installed
import importlib
import sys

_redis_mock = MagicMock()
_orig_redis = sys.modules.get("redis")
sys.modules["redis"] = _redis_mock

# Force reimport to pick up mock redis
import app.services.cache.redis_cache as redis_cache_mod

# Restore
if _orig_redis is not None:
    sys.modules["redis"] = _orig_redis
else:
    del sys.modules["redis"]

from app.services.cache.redis_cache import (
    RedisCache, RedisCacheManager, CacheManager, CacheKeys,
    cache_key, cache_result,
)


class TestRedisCache(unittest.TestCase):

    def _make_cache(self):
        """Create a RedisCache with mocked client"""
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            with patch.object(redis_cache_mod, "redis") as mock_redis_mod:
                mock_client = MagicMock()
                mock_redis_mod.Redis.return_value = mock_client
                mock_client.ping.return_value = True
                cache = RedisCache.__new__(RedisCache)
                cache.host = "localhost"
                cache.port = 6379
                cache.db = 0
                cache.password = None
                cache.decode_responses = False
                cache.client = mock_client
                return cache

    # --- is_available ---
    def test_is_available_true(self):
        cache = self._make_cache()
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertTrue(cache.is_available())

    def test_is_available_no_client(self):
        cache = self._make_cache()
        cache.client = None
        self.assertFalse(cache.is_available())

    # --- set ---
    def test_set_success(self):
        cache = self._make_cache()
        cache.client.set.return_value = True
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertTrue(cache.set("key", {"a": 1}, expire=60))

    def test_set_unavailable(self):
        cache = self._make_cache()
        cache.client = None
        self.assertFalse(cache.set("key", "val"))

    def test_set_exception(self):
        cache = self._make_cache()
        cache.client.set.side_effect = Exception("fail")
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertFalse(cache.set("key", "val"))

    # --- get ---
    def test_get_success(self):
        cache = self._make_cache()
        cache.client.get.return_value = b'{"a": 1}'
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertEqual(cache.get("key"), {"a": 1})

    def test_get_none(self):
        cache = self._make_cache()
        cache.client.get.return_value = None
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertIsNone(cache.get("key"))

    def test_get_unavailable(self):
        cache = self._make_cache()
        cache.client = None
        self.assertIsNone(cache.get("key"))

    # --- delete ---
    def test_delete_success(self):
        cache = self._make_cache()
        cache.client.delete.return_value = 1
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertTrue(cache.delete("key"))

    def test_delete_unavailable(self):
        cache = self._make_cache()
        cache.client = None
        self.assertFalse(cache.delete("key"))

    # --- exists ---
    def test_exists_true(self):
        cache = self._make_cache()
        cache.client.exists.return_value = 1
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertTrue(cache.exists("key"))

    def test_exists_false(self):
        cache = self._make_cache()
        cache.client.exists.return_value = 0
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertFalse(cache.exists("key"))

    # --- clear_pattern ---
    def test_clear_pattern_with_keys(self):
        cache = self._make_cache()
        cache.client.keys.return_value = [b"k1", b"k2"]
        cache.client.delete.return_value = 2
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertEqual(cache.clear_pattern("k*"), 2)

    def test_clear_pattern_no_keys(self):
        cache = self._make_cache()
        cache.client.keys.return_value = []
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertEqual(cache.clear_pattern("k*"), 0)

    # --- increment ---
    def test_increment(self):
        cache = self._make_cache()
        cache.client.incr.return_value = 5
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertEqual(cache.increment("counter", 1), 5)

    def test_increment_unavailable(self):
        cache = self._make_cache()
        cache.client = None
        self.assertIsNone(cache.increment("counter"))

    # --- expire ---
    def test_expire_success(self):
        cache = self._make_cache()
        cache.client.expire.return_value = True
        with patch.object(redis_cache_mod, "REDIS_AVAILABLE", True):
            self.assertTrue(cache.expire("key", 60))

    def test_expire_unavailable(self):
        cache = self._make_cache()
        cache.client = None
        self.assertFalse(cache.expire("key", 60))


class TestCacheKey(unittest.TestCase):
    def test_cache_key(self):
        self.assertEqual(cache_key("user", 1, "profile"), "user:1:profile")


class TestCacheKeys(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(CacheKeys.PROJECT, "project")
        self.assertEqual(CacheKeys.ALERT_STATS, "alert:stats")


class TestCacheManagerAlias(unittest.TestCase):
    def test_alias(self):
        self.assertIs(CacheManager, RedisCacheManager)


class TestRedisCacheManager(unittest.TestCase):

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_project_cache_specific(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_project_cache(project_id=1)
        self.assertTrue(mock_cache.clear_pattern.called)

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_project_cache_all(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_project_cache()
        self.assertTrue(mock_cache.clear_pattern.called)

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_user_cache(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_user_cache(user_id=1)
        self.assertTrue(mock_cache.clear_pattern.called)

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_user_cache_all(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_user_cache()
        self.assertTrue(mock_cache.clear_pattern.called)

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_alert_cache(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_alert_cache()
        self.assertTrue(mock_cache.clear_pattern.called)

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_search_cache(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_search_cache()
        mock_cache.clear_pattern.assert_called()

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_dashboard_cache(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_dashboard_cache()
        mock_cache.clear_pattern.assert_called()

    @patch.object(redis_cache_mod, "get_cache")
    def test_clear_all_cache(self, mock_get_cache):
        mock_cache = MagicMock()
        mock_cache.is_available.return_value = True
        mock_get_cache.return_value = mock_cache
        RedisCacheManager.clear_all_cache()
        mock_cache.client.flushdb.assert_called_once()


if __name__ == "__main__":
    unittest.main()
