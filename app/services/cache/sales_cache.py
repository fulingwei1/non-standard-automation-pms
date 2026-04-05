# -*- coding: utf-8 -*-
"""
销售模块缓存服务

为销售模块提供专用的缓存操作，包括：
- 商机列表/详情缓存
- 合同列表/详情缓存
- 报价列表/详情缓存
- 销售统计缓存
- 销售漏斗缓存
"""

import logging
from functools import wraps
from typing import Callable, Optional

from app.core.config import settings

from .redis_cache import CacheKeys, RedisCache, cache_key

logger = logging.getLogger(__name__)

# 默认缓存过期时间（秒）
DEFAULT_CACHE_TTL = getattr(settings, "REDIS_CACHE_DEFAULT_TTL", 300)  # 5分钟
LIST_CACHE_TTL = 60  # 列表缓存1分钟
STATS_CACHE_TTL = 180  # 统计缓存3分钟


class SalesCacheService:
    """销售模块缓存服务"""

    def __init__(self, cache: Optional[RedisCache] = None):
        """
        初始化销售缓存服务

        Args:
            cache: Redis缓存实例，如果为None则尝试创建
        """
        self.cache = cache
        if self.cache is None:
            self._init_cache()

    def _init_cache(self) -> None:
        """初始化缓存连接"""
        if not getattr(settings, "REDIS_CACHE_ENABLED", False):
            logger.debug("Redis缓存未启用")
            return

        try:
            redis_url = getattr(settings, "REDIS_URL", None)
            if redis_url:
                # 从URL解析连接信息
                from urllib.parse import urlparse
                parsed = urlparse(redis_url)
                self.cache = RedisCache(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 6379,
                    password=parsed.password,
                    db=int(parsed.path.lstrip("/") or 0),
                )
            else:
                self.cache = RedisCache()
        except Exception as e:
            logger.warning(f"初始化Redis缓存失败: {e}")
            self.cache = None

    def is_available(self) -> bool:
        """检查缓存是否可用"""
        return self.cache is not None and self.cache.is_available()

    # ========== 商机缓存 ==========

    def get_opportunity(self, opportunity_id: int) -> Optional[dict]:
        """获取商机缓存"""
        if not self.is_available():
            return None
        key = cache_key(CacheKeys.SALES_OPPORTUNITY, opportunity_id)
        return self.cache.get(key)

    def set_opportunity(self, opportunity_id: int, data: dict, ttl: int = DEFAULT_CACHE_TTL) -> bool:
        """设置商机缓存"""
        if not self.is_available():
            return False
        key = cache_key(CacheKeys.SALES_OPPORTUNITY, opportunity_id)
        return self.cache.set(key, data, expire=ttl)

    def invalidate_opportunity(self, opportunity_id: int) -> bool:
        """使商机缓存失效"""
        if not self.is_available():
            return False
        key = cache_key(CacheKeys.SALES_OPPORTUNITY, opportunity_id)
        # 同时清除列表缓存
        self.cache.clear_pattern(f"{CacheKeys.SALES_OPPORTUNITY_LIST}:*")
        return self.cache.delete(key)

    def get_opportunity_stats(self) -> Optional[dict]:
        """获取商机统计缓存"""
        if not self.is_available():
            return None
        key = CacheKeys.SALES_OPPORTUNITY_STATS
        return self.cache.get(key)

    def set_opportunity_stats(self, data: dict, ttl: int = STATS_CACHE_TTL) -> bool:
        """设置商机统计缓存"""
        if not self.is_available():
            return False
        return self.cache.set(CacheKeys.SALES_OPPORTUNITY_STATS, data, expire=ttl)

    # ========== 合同缓存 ==========

    def get_contract(self, contract_id: int) -> Optional[dict]:
        """获取合同缓存"""
        if not self.is_available():
            return None
        key = cache_key(CacheKeys.SALES_CONTRACT, contract_id)
        return self.cache.get(key)

    def set_contract(self, contract_id: int, data: dict, ttl: int = DEFAULT_CACHE_TTL) -> bool:
        """设置合同缓存"""
        if not self.is_available():
            return False
        key = cache_key(CacheKeys.SALES_CONTRACT, contract_id)
        return self.cache.set(key, data, expire=ttl)

    def invalidate_contract(self, contract_id: int) -> bool:
        """使合同缓存失效"""
        if not self.is_available():
            return False
        key = cache_key(CacheKeys.SALES_CONTRACT, contract_id)
        # 同时清除列表缓存和统计缓存
        self.cache.clear_pattern(f"{CacheKeys.SALES_CONTRACT_LIST}:*")
        self.cache.delete(CacheKeys.SALES_CONTRACT_STATS)
        return self.cache.delete(key)

    def get_contract_stats(self) -> Optional[dict]:
        """获取合同统计缓存"""
        if not self.is_available():
            return None
        return self.cache.get(CacheKeys.SALES_CONTRACT_STATS)

    def set_contract_stats(self, data: dict, ttl: int = STATS_CACHE_TTL) -> bool:
        """设置合同统计缓存"""
        if not self.is_available():
            return False
        return self.cache.set(CacheKeys.SALES_CONTRACT_STATS, data, expire=ttl)

    # ========== 销售漏斗缓存 ==========

    def get_funnel_stats(self, user_id: Optional[int] = None) -> Optional[dict]:
        """获取销售漏斗统计缓存"""
        if not self.is_available():
            return None
        key = cache_key(CacheKeys.SALES_FUNNEL, user_id or "all")
        return self.cache.get(key)

    def set_funnel_stats(self, data: dict, user_id: Optional[int] = None, ttl: int = STATS_CACHE_TTL) -> bool:
        """设置销售漏斗统计缓存"""
        if not self.is_available():
            return False
        key = cache_key(CacheKeys.SALES_FUNNEL, user_id or "all")
        return self.cache.set(key, data, expire=ttl)

    def invalidate_funnel_stats(self) -> int:
        """使所有销售漏斗缓存失效"""
        if not self.is_available():
            return 0
        return self.cache.clear_pattern(f"{CacheKeys.SALES_FUNNEL}:*")

    # ========== 应收账款缓存 ==========

    def get_receivables_summary(self) -> Optional[dict]:
        """获取应收账款汇总缓存"""
        if not self.is_available():
            return None
        return self.cache.get(CacheKeys.SALES_RECEIVABLES)

    def set_receivables_summary(self, data: dict, ttl: int = STATS_CACHE_TTL) -> bool:
        """设置应收账款汇总缓存"""
        if not self.is_available():
            return False
        return self.cache.set(CacheKeys.SALES_RECEIVABLES, data, expire=ttl)

    def invalidate_receivables(self) -> bool:
        """使应收账款缓存失效"""
        if not self.is_available():
            return False
        return self.cache.delete(CacheKeys.SALES_RECEIVABLES)

    # ========== 销售仪表盘缓存 ==========

    def get_dashboard(self, user_id: int) -> Optional[dict]:
        """获取销售仪表盘缓存"""
        if not self.is_available():
            return None
        key = cache_key(CacheKeys.SALES_DASHBOARD, user_id)
        return self.cache.get(key)

    def set_dashboard(self, user_id: int, data: dict, ttl: int = LIST_CACHE_TTL) -> bool:
        """设置销售仪表盘缓存"""
        if not self.is_available():
            return False
        key = cache_key(CacheKeys.SALES_DASHBOARD, user_id)
        return self.cache.set(key, data, expire=ttl)

    def invalidate_dashboard(self, user_id: Optional[int] = None) -> int:
        """使销售仪表盘缓存失效"""
        if not self.is_available():
            return 0
        if user_id:
            key = cache_key(CacheKeys.SALES_DASHBOARD, user_id)
            return 1 if self.cache.delete(key) else 0
        else:
            return self.cache.clear_pattern(f"{CacheKeys.SALES_DASHBOARD}:*")

    # ========== 批量清除 ==========

    def invalidate_all_sales_cache(self) -> int:
        """清除所有销售模块缓存"""
        if not self.is_available():
            return 0
        return self.cache.clear_pattern("sales:*")


def cache_result(
    key_prefix: str,
    ttl: int = DEFAULT_CACHE_TTL,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    缓存装饰器

    用于缓存函数返回结果。

    Args:
        key_prefix: 缓存键前缀
        ttl: 缓存过期时间（秒）
        key_builder: 自定义键构建函数，接收原函数的参数

    Example:
        @cache_result("sales:opportunity:stats", ttl=180)
        def get_opportunity_statistics(db, user_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试获取缓存服务
            cache_service = SalesCacheService()
            if not cache_service.is_available():
                return func(*args, **kwargs)

            # 构建缓存键
            if key_builder:
                cache_key_str = cache_key(key_prefix, key_builder(*args, **kwargs))
            else:
                # 默认使用函数名和参数哈希
                import hashlib
                params_str = str(args[1:]) + str(sorted(kwargs.items()))
                params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
                cache_key_str = cache_key(key_prefix, params_hash)

            # 尝试从缓存获取
            cached = cache_service.cache.get(cache_key_str)
            if cached is not None:
                logger.debug(f"缓存命中: {cache_key_str}")
                return cached

            # 执行原函数
            result = func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                cache_service.cache.set(cache_key_str, result, expire=ttl)
                logger.debug(f"缓存存储: {cache_key_str}")

            return result
        return wrapper
    return decorator


# 创建全局缓存服务实例
_sales_cache_instance: Optional[SalesCacheService] = None


def get_sales_cache() -> SalesCacheService:
    """获取销售缓存服务单例"""
    global _sales_cache_instance
    if _sales_cache_instance is None:
        _sales_cache_instance = SalesCacheService()
    return _sales_cache_instance
