# -*- coding: utf-8 -*-
"""
统一缓存入口 (#30)

缓存系统架构：
- CacheService: 通用缓存服务，Redis + 内存降级（推荐入口）
- RedisCache / get_cache: 纯 Redis 缓存操作
- BusinessCacheService: 业务层缓存（基于 RedisCache）
- DashboardCacheService: 仪表盘缓存（已委托 CacheService）
- cache_response 装饰器: API 端点缓存（已委托 CacheService）
- ReportCacheManager: 报表框架专用缓存

推荐用法：
    from app.services.cache import CacheService, cache_response

    # 通用缓存
    cache = CacheService()
    cache.set("key", value, ttl=300)

    # 装饰器
    @cache_response(prefix="my_api", ttl=600)
    def my_endpoint(...): ...
"""

from app.services.cache.redis_cache import RedisCache, CacheKeys, cache_key, get_cache
from app.services.cache.business_cache import BusinessCacheService
from app.services.cache_service import CacheService
from app.utils.cache_decorator import cache_response, get_cache_service

__all__ = [
    "CacheService",
    "RedisCache",
    "CacheKeys",
    "cache_key",
    "get_cache",
    "BusinessCacheService",
    "cache_response",
    "get_cache_service",
]
