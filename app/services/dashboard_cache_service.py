# -*- coding: utf-8 -*-
"""
仪表盘缓存服务

REFACTORED (#30): 内部委托给通用 CacheService 获取 redis_client，
消除重复的 Redis 连接管理。保留原有接口以保持向后兼容。
"""

import json
import logging
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


class DashboardCacheService:
    """仪表盘缓存服务 — 复用 CacheService 的 redis_client"""

    def __init__(self, redis_url: Optional[str] = None, ttl: int = 300):
        self.ttl = ttl
        self._cache = CacheService()
        # 向后兼容：暴露 redis_client 属性
        self.redis_client = getattr(self._cache, 'redis_client', None)
        self.cache_enabled = self.redis_client is not None

    def _get_cache_key(self, key_prefix: str, **kwargs) -> str:
        parts = [key_prefix]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return ":".join(parts)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        if not self.cache_enabled or not self.redis_client:
            return None
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.debug(f"读取缓存失败: {e}")
        return None

    def set(self, key: str, data: Dict[str, Any]) -> bool:
        if not self.cache_enabled or not self.redis_client:
            return False
        try:
            self.redis_client.setex(
                key,
                timedelta(seconds=self.ttl),
                json.dumps(data, ensure_ascii=False, default=str)
            )
            return True
        except Exception as e:
            logger.debug(f"设置缓存失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        if not self.cache_enabled or not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.debug(f"删除缓存失败: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        if not self.cache_enabled or not self.redis_client:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            logger.debug(f"批量删除缓存失败: {e}")
        return 0

    def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Dict[str, Any]],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        if not force_refresh:
            cached = self.get(key)
            if cached is not None:
                return cached
        data = fetch_func()
        self.set(key, data)
        return data


# ── 全局实例 & 兼容函数 ──────────────────────────────
_cache_instance: Optional[DashboardCacheService] = None


def get_cache_service(
    redis_url: Optional[str] = None,
    ttl: int = 300
) -> DashboardCacheService:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DashboardCacheService(redis_url=redis_url, ttl=ttl)
    return _cache_instance


def invalidate_dashboard_cache(pattern: str = "dashboard:*") -> int:
    cache = get_cache_service()
    return cache.clear_pattern(pattern)


# ── Re-exports for unified cache access (#30) ────────────────────────
from app.services.cache_service import CacheService as UnifiedCacheService  # noqa: F401, E402
from app.services.cache.redis_cache import RedisCache, RedisCacheManager  # noqa: F401, E402
from app.utils.cache_decorator import cache_response  # noqa: F401, E402
