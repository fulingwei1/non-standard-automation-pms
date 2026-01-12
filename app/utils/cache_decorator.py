# -*- coding: utf-8 -*-
"""
缓存装饰器工具
提供统一的缓存装饰器，用于API端点缓存
"""

import functools
import logging
from typing import Callable, Optional, Any, Dict
from datetime import datetime

from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# 全局缓存服务实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    获取缓存服务实例（单例）

    Returns:
        CacheService: 缓存服务实例
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cache_response(
    prefix: str,
    ttl: int = 300,
    key_func: Optional[Callable] = None,
    invalidate_func: Optional[Callable] = None,
):
    """
    响应缓存装饰器

    Args:
        prefix: 缓存键前缀
        ttl: 缓存过期时间（秒）
        key_func: 自定义缓存键生成函数，默认使用参数生成
        invalidate_func: 缓存失效函数，在更新/删除操作时调用

    Usage:
        @cache_response("project:list", ttl=300)
        async def get_project_list(filters: dict):
            return db.query(Project).filter_by(**filters).all()
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            cache_service = get_cache_service()

            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 使用函数名和参数生成键
                import json
                import hashlib
                params_str = json.dumps(kwargs, sort_keys=True, default=str)
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                cache_key = f"{prefix}:{params_hash}"

            # 尝试从缓存获取
            cached_data = cache_service.get(cache_key)
            if cached_data is not None:
                logger.debug(f"缓存命中: {cache_key}")
                # 添加缓存标识
                if isinstance(cached_data, dict):
                    cached_data["_from_cache"] = True
                return cached_data

            # 缓存未命中，执行函数
            logger.debug(f"缓存未命中: {cache_key}")
            result = func(*args, **kwargs)

            # 存入缓存
            cache_service.set(cache_key, result, expire_seconds=ttl)

            # 添加缓存标识
            if isinstance(result, dict):
                result["_from_cache"] = False

            return result

        # 添加缓存失效方法
        wrapper.invalidate_cache = lambda *args, **kwargs: (
            invalidate_func(*args, **kwargs) if invalidate_func else None
        )

        return wrapper

    return decorator


def cache_project_detail(func: Callable):
    """
    项目详情缓存装饰器

    Args:
        func: 要缓存的函数，必须接受 project_id 作为参数

    Usage:
        @cache_project_detail
        async def get_project_detail(project_id: int, db: Session):
            return db.query(Project).filter(Project.id == project_id).first()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_service = get_cache_service()

        # 提取 project_id
        project_id = kwargs.get("project_id") or (args[1] if len(args) > 1 else None)
        if project_id is None:
            # 无法确定项目ID，直接执行函数
            return func(*args, **kwargs)

        # 尝试从缓存获取
        cached_data = cache_service.get_project_detail(project_id)
        if cached_data is not None:
            logger.debug(f"项目详情缓存命中: {project_id}")
            if isinstance(cached_data, dict):
                cached_data["_from_cache"] = True
            return cached_data

        # 缓存未命中，执行函数
        logger.debug(f"项目详情缓存未命中: {project_id}")
        result = func(*args, **kwargs)

        # 存入缓存
        if result:
            # 转换为字典（如果是ORM对象）
            if hasattr(result, '__dict__'):
                result_dict = {
                    column.name: getattr(result, column.name)
                    for column in result.__table__.columns
                }
                cache_service.set_project_detail(project_id, result_dict)
            else:
                cache_service.set_project_detail(project_id, result)

            if isinstance(result, dict):
                result["_from_cache"] = False

        return result

    # 添加缓存失效方法
    wrapper.invalidate = lambda project_id: cache_service.invalidate_project_detail(project_id)

    return wrapper


def cache_project_list(func: Callable):
    """
    项目列表缓存装饰器

    Args:
        func: 要缓存的函数，必须接受 filters 作为参数

    Usage:
        @cache_project_list
        async def get_project_list(filters: dict, db: Session):
            return db.query(Project).filter_by(**filters).all()
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        cache_service = get_cache_service()

        # 提取 filters
        filters = kwargs.get("filters") or (args[1] if len(args) > 1 else {})
        if not isinstance(filters, dict):
            filters = {}

        # 尝试从缓存获取
        cached_data = cache_service.get_project_list(**filters)
        if cached_data is not None:
            logger.debug(f"项目列表缓存命中: {filters}")
            if isinstance(cached_data, dict):
                cached_data["_from_cache"] = True
            return cached_data

        # 缓存未命中，执行函数
        logger.debug(f"项目列表缓存未命中: {filters}")
        result = func(*args, **kwargs)

        # 存入缓存
        if result:
            cache_service.set_project_list(result, **filters)

            if isinstance(result, dict):
                result["_from_cache"] = False

        return result

    # 添加缓存失效方法
    wrapper.invalidate = lambda: cache_service.invalidate_project_list()

    return wrapper


def cache_with_prefix(prefix: str, ttl: int = 300):
    """
    自定义前缀缓存装饰器

    Args:
        prefix: 缓存键前缀
        ttl: 缓存过期时间（秒）

    Usage:
        @cache_with_prefix("user:permissions", ttl=3600)
        async def get_user_permissions(user_id: int):
            return get_permissions(user_id)
    """
    return cache_response(prefix=prefix, ttl=ttl)


def log_query_time(threshold: float = 0.5):
    """
    查询性能日志装饰器

    Args:
        threshold: 超过此阈值（秒）时记录为慢查询

    Usage:
        @log_query_time(threshold=0.5)
        async def get_project_list(filters: dict):
            return db.query(Project).all()
    """
    import time

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start

            if elapsed > threshold:
                logger.warning(
                    f"慢查询: {func.__name__} "
                    f"参数={kwargs} "
                    f"耗时={elapsed:.3f}s"
                )

            return result
        return wrapper
    return decorator


class QueryStats:
    """查询统计类"""

    def __init__(self):
        self.reset()

    def reset(self):
        """重置统计"""
        self.queries = []
        self.total_time = 0
        self.slow_queries = []
        self.cache_hits = 0
        self.cache_misses = 0

    def record_query(self, func_name: str, elapsed: float, params: dict = None):
        """记录查询"""
        self.queries.append({
            "function": func_name,
            "elapsed": elapsed,
            "params": params,
            "timestamp": datetime.now().isoformat(),
        })
        self.total_time += elapsed

        if elapsed > 0.5:
            self.slow_queries.append({
                "function": func_name,
                "elapsed": elapsed,
                "params": params,
            })

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_queries": len(self.queries),
            "total_time": round(self.total_time, 3),
            "avg_time": round(self.total_time / len(self.queries), 3) if self.queries else 0,
            "slow_queries": len(self.slow_queries),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(
                self.cache_hits / (self.cache_hits + self.cache_misses) * 100, 2
            ) if (self.cache_hits + self.cache_misses) > 0 else 0,
        }


# 全局查询统计实例
query_stats = QueryStats()


def track_query(func: Callable):
    """
    查询追踪装饰器（用于监控）

    Usage:
        @track_query
        async def get_project_list(filters: dict):
            return db.query(Project).all()
    """
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        query_stats.record_query(
            func_name=func.__name__,
            elapsed=elapsed,
            params=kwargs
        )

        return result
    return wrapper
