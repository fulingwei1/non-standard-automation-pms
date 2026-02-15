# -*- coding: utf-8 -*-
"""
仪表盘缓存服务
提供Redis缓存支持，缓存5分钟
"""

import json
from datetime import timedelta
from typing import Any, Callable, Dict, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class DashboardCacheService:
    """仪表盘缓存服务"""

    def __init__(self, redis_url: Optional[str] = None, ttl: int = 300):
        """
        初始化缓存服务
        
        Args:
            redis_url: Redis连接URL，如果为None或Redis不可用则禁用缓存
            ttl: 缓存TTL（秒），默认300秒（5分钟）
        """
        self.ttl = ttl
        self.redis_client = None
        self.cache_enabled = False
        
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                # 测试连接
                self.redis_client.ping()
                self.cache_enabled = True
            except Exception as e:
                print(f"Redis连接失败，缓存已禁用: {e}")
                self.cache_enabled = False
        else:
            print("Redis不可用或未配置，缓存已禁用")

    def _get_cache_key(self, key_prefix: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            key_prefix: 键前缀
            **kwargs: 其他参数
            
        Returns:
            str: 缓存键
        """
        parts = [key_prefix]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}:{v}")
        return ":".join(parts)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存数据
        
        Args:
            key: 缓存键
            
        Returns:
            dict or None: 缓存的数据，如果不存在或缓存禁用则返回None
        """
        if not self.cache_enabled or not self.redis_client:
            return None
        
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            print(f"读取缓存失败: {e}")
        
        return None

    def set(self, key: str, data: Dict[str, Any]) -> bool:
        """
        设置缓存数据
        
        Args:
            key: 缓存键
            data: 要缓存的数据
            
        Returns:
            bool: 是否成功
        """
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
            print(f"设置缓存失败: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否成功
        """
        if not self.cache_enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"删除缓存失败: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存
        
        Args:
            pattern: 模式，如 "dashboard:*"
            
        Returns:
            int: 删除的键数量
        """
        if not self.cache_enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            print(f"批量删除缓存失败: {e}")
        
        return 0

    def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Dict[str, Any]],
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        获取缓存或执行函数并缓存结果
        
        Args:
            key: 缓存键
            fetch_func: 获取数据的函数
            force_refresh: 是否强制刷新
            
        Returns:
            dict: 数据
        """
        # 如果不强制刷新，尝试从缓存获取
        if not force_refresh:
            cached_data = self.get(key)
            if cached_data is not None:
                return cached_data
        
        # 执行函数获取数据
        data = fetch_func()
        
        # 缓存数据
        self.set(key, data)
        
        return data


# 全局缓存实例（可在应用启动时配置）
_cache_instance: Optional[DashboardCacheService] = None


def get_cache_service(
    redis_url: Optional[str] = None,
    ttl: int = 300
) -> DashboardCacheService:
    """
    获取缓存服务实例
    
    Args:
        redis_url: Redis连接URL
        ttl: 缓存TTL（秒）
        
    Returns:
        DashboardCacheService: 缓存服务实例
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = DashboardCacheService(redis_url=redis_url, ttl=ttl)
    
    return _cache_instance


def invalidate_dashboard_cache(pattern: str = "dashboard:*") -> int:
    """
    清除仪表盘缓存
    
    Args:
        pattern: 缓存键模式
        
    Returns:
        int: 删除的键数量
    """
    cache = get_cache_service()
    return cache.clear_pattern(pattern)
