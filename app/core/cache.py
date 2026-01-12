# -*- coding: utf-8 -*-
"""
Redis缓存管理模块
提供高效的缓存装饰器和工具函数
"""

import json
from typing import Any, Callable, Optional, Union, TypeVar
from functools import wraps
from hashlib import md5

from app.core.config import settings

T = TypeVar('T')


class CacheManager:
    """Redis缓存管理器"""

    def __init__(self):
        self._client = None

    def get_client(self):
        """获取Redis客户端（懒加载）"""
        if self._client is None and settings.REDIS_CACHE_ENABLED and settings.REDIS_URL:
            try:
                import redis
                self._client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_timeout=5,
                    socket_connect_timeout=5
                )
            except ImportError:
                print("警告: redis包未安装，缓存功能不可用")
            except Exception as e:
                print(f"警告: Redis连接失败，缓存功能不可用: {e}")
        return self._client

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        client = self.get_client()
        if not client:
            return None

        try:
            value = client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"缓存读取失败: {e}")
        return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        client = self.get_client()
        if not client:
            return False

        try:
            ttl = ttl or settings.REDIS_CACHE_DEFAULT_TTL
            client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"缓存写入失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        client = self.get_client()
        if not client:
            return False

        try:
            client.delete(key)
            return True
        except Exception as e:
            print(f"缓存删除失败: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的所有缓存"""
        client = self.get_client()
        if not client:
            return 0

        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            print(f"批量缓存删除失败: {e}")
            return 0

    def clear_all(self) -> bool:
        """清空所有缓存"""
        client = self.get_client()
        if not client:
            return False

        try:
            client.flushdb()
            return True
        except Exception as e:
            print(f"清空缓存失败: {e}")
            return False


# 全局缓存管理器实例
cache_manager = CacheManager()


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成缓存键

    Args:
        prefix: 缓存键前缀
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        缓存键字符串
    """
    # 过滤掉不需要缓存的参数（如db session）
    filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['db', 'session']}
    key_data = f"{prefix}:{str(args)}:{str(sorted(filtered_kwargs.items()))}"
    return f"{prefix}:{md5(key_data.encode()).hexdigest()}"


def cached(
    prefix: str,
    ttl: Optional[int] = None,
    skip_args: Optional[list] = None
):
    """
    缓存装饰器

    Args:
        prefix: 缓存键前缀
        ttl: 缓存过期时间（秒），默认使用配置
        skip_args: 跳过缓存的参数名列表

    Usage:
        @cached(prefix="user", ttl=300)
        def get_user(user_id: int):
            return db.query(User).get(user_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 如果Redis未启用，直接调用原函数
            if not settings.REDIS_CACHE_ENABLED or not settings.REDIS_URL:
                return func(*args, **kwargs)

            # 生成缓存键
            cache_key = _generate_cache_key(prefix, *args, **kwargs)

            # 尝试从缓存获取
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行原函数
            result = func(*args, **kwargs)

            # 将结果存入缓存
            if result is not None:
                cache_manager.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    使缓存失效

    Args:
        pattern: 缓存键模式（支持通配符*）

    Usage:
        invalidate_cache("project:*")
    """
    if settings.REDIS_CACHE_ENABLED and settings.REDIS_URL:
        cache_manager.delete_pattern(pattern)


# 常用缓存键前缀常量
CACHE_PREFIXES = {
    "PROJECT_LIST": "project:list",
    "PROJECT_DETAIL": "project:detail",
    "PROJECT_STATS": "project:stats",
    "USER_LIST": "user:list",
    "USER_DETAIL": "user:detail",
    "MATERIAL_LIST": "material:list",
    "MATERIAL_DETAIL": "material:detail",
    "BOM_LIST": "bom:list",
    "ORDER_LIST": "order:list",
    "ORDER_DETAIL": "order:detail",
    "DASHBOARD_STATS": "dashboard:stats",
    "REPORT_DATA": "report:data",
}


class QueryOptimizer:
    """查询优化辅助类"""

    @staticmethod
    def with_pagination(query, page: int = 1, page_size: int = None):
        """
        添加分页

        Args:
            query: SQLAlchemy查询对象
            page: 页码
            page_size: 每页数量

        Returns:
            分页后的查询对象
        """
        page_size = page_size or settings.DEFAULT_PAGE_SIZE
        page_size = min(page_size, settings.MAX_PAGE_SIZE)
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)

    @staticmethod
    def cache_result(cache_key: str, result: Any, ttl: int = None):
        """
        缓存查询结果

        Args:
            cache_key: 缓存键
            result: 结果数据
            ttl: 缓存过期时间
        """
        if settings.REDIS_CACHE_ENABLED and settings.REDIS_URL:
            cache_manager.set(cache_key, result, ttl=ttl)

    @staticmethod
    def get_cached_result(cache_key: str) -> Optional[Any]:
        """
        获取缓存结果

        Args:
            cache_key: 缓存键

        Returns:
            缓存的数据或None
        """
        if settings.REDIS_CACHE_ENABLED and settings.REDIS_URL:
            return cache_manager.get(cache_key)
        return None


# 导出主要接口
__all__ = [
    'CacheManager',
    'cache_manager',
    'cached',
    'invalidate_cache',
    'CACHE_PREFIXES',
    'QueryOptimizer',
]
