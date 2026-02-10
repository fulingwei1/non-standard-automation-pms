# -*- coding: utf-8 -*-
"""
报表缓存管理器

支持内存缓存和 Redis 缓存。
专用于报表框架的缓存管理。
"""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.services.report_framework.models import ReportConfig


class CacheBackend(ABC):
    """缓存后端抽象基类"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> None:
        """设置缓存"""
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除缓存"""
        pass

    @abstractmethod
    def clear(self, pattern: Optional[str] = None) -> None:
        """清除缓存"""
        pass


class MemoryCacheBackend(CacheBackend):
    """
    内存缓存后端

    简单的字典缓存，支持 TTL
    """

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在或已过期返回 None
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            # 已过期，删除
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl: int) -> None:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），0 表示永不过期
        """
        expires_at = time.time() + ttl if ttl > 0 else None
        self._cache[key] = {
            "value": value,
            "expires_at": expires_at,
            "created_at": time.time(),
        }

    def delete(self, key: str) -> None:
        """
        删除缓存

        Args:
            key: 缓存键
        """
        self._cache.pop(key, None)

    def clear(self, pattern: Optional[str] = None) -> None:
        """
        清除缓存

        Args:
            pattern: 键名模式（简单前缀匹配）
        """
        if pattern:
            # 简单前缀匹配
            prefix = pattern.replace("*", "")
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
        else:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的数量
        """
        now = time.time()
        expired_keys = [
            k for k, v in self._cache.items()
            if v["expires_at"] and now > v["expires_at"]
        ]
        for k in expired_keys:
            del self._cache[k]
        return len(expired_keys)


class RedisCacheBackend(CacheBackend):
    """
    Redis 缓存后端

    使用 Redis 作为缓存存储
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0", prefix: str = "report:"):
        """
        初始化 Redis 缓存后端

        Args:
            redis_url: Redis 连接 URL
            prefix: 键名前缀
        """
        self._prefix = prefix
        self._redis = None
        self._redis_url = redis_url

    def _get_redis(self):
        """延迟加载 Redis 连接"""
        if self._redis is None:
            try:
                import redis
                self._redis = redis.from_url(self._redis_url)
            except ImportError:
                raise RuntimeError("redis package is required for Redis cache backend")
        return self._redis

    def _key(self, key: str) -> str:
        """添加键名前缀"""
        return f"{self._prefix}{key}"

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            data = self._get_redis().get(self._key(key))
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int) -> None:
        """设置缓存"""
        try:
            data = json.dumps(value, default=str)
            if ttl > 0:
                self._get_redis().setex(self._key(key), ttl, data)
            else:
                self._get_redis().set(self._key(key), data)
        except Exception:
            pass  # 缓存失败不应该影响主流程

    def delete(self, key: str) -> None:
        """删除缓存"""
        try:
            self._get_redis().delete(self._key(key))
        except Exception:
            pass

    def clear(self, pattern: Optional[str] = None) -> None:
        """清除缓存"""
        try:
            r = self._get_redis()
            if pattern:
                keys = r.keys(self._key(pattern))
            else:
                keys = r.keys(f"{self._prefix}*")
            if keys:
                r.delete(*keys)
        except Exception:
            pass


class ReportCacheManager:
    """
    缓存管理器

    协调缓存后端，处理缓存键生成
    """

    def __init__(self, backend: Optional[CacheBackend] = None):
        """
        初始化报表缓存管理器

        Args:
            backend: 缓存后端，默认使用内存缓存
        """
        self._backend = backend or MemoryCacheBackend()

    def get(self, config: ReportConfig, params: Dict[str, Any]) -> Optional[Any]:
        """
        获取缓存的报告结果

        Args:
            config: 报告配置
            params: 报告参数

        Returns:
            缓存的结果，不存在返回 None
        """
        if not config.cache.enabled:
            return None

        key = self._generate_key(config, params)
        return self._backend.get(key)

    def set(self, config: ReportConfig, params: Dict[str, Any], result: Any) -> None:
        """
        缓存报告结果

        Args:
            config: 报告配置
            params: 报告参数
            result: 报告结果
        """
        if not config.cache.enabled:
            return

        key = self._generate_key(config, params)
        self._backend.set(key, result, config.cache.ttl)

    def invalidate(self, report_code: str) -> None:
        """
        使指定报告的缓存失效

        Args:
            report_code: 报告代码
        """
        self._backend.clear(f"report:{report_code}:*")

    def clear_all(self) -> None:
        """清除所有缓存"""
        self._backend.clear()

    def _generate_key(self, config: ReportConfig, params: Dict[str, Any]) -> str:
        """
        生成缓存键

        Args:
            config: 报告配置
            params: 报告参数

        Returns:
            缓存键
        """
        if config.cache.key_pattern:
            # 使用配置的键模式
            key = config.cache.key_pattern
            key = key.replace("{code}", config.meta.code)
            for k, v in params.items():
                key = key.replace(f"{{{k}}}", str(v))
            return key

        # 默认键生成
        params_hash = hashlib.md5(
            json.dumps(params, sort_keys=True, default=str).encode()
        ).hexdigest()[:8]

        return f"report:{config.meta.code}:{params_hash}"


# 向后兼容别名，保留 CacheManager 名称以减少破坏性变更
# DEPRECATED: 请使用 ReportCacheManager，CacheManager 别名仅用于向后兼容
CacheManager = ReportCacheManager
