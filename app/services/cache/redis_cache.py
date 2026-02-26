# -*- coding: utf-8 -*-
"""
Redis缓存服务

提供基于Redis的缓存操作
"""

import json
import logging
from typing import Any, List, Optional

logger = logging.getLogger(__name__)

# 尝试导入Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None


class CacheKeys:
    """缓存键常量"""
    PROJECT = "project"
    PROJECT_LIST = "project:list"
    PROJECT_DASHBOARD = "project:dashboard"
    PROJECT_STATS = "project:stats"
    USER = "user"
    USER_PERMISSIONS = "user:permissions"
    ALERT = "alert"
    ALERT_STATS = "alert:stats"
    SEARCH = "search"
    CONFIG = "config"
    REPORT = "report"


def cache_key(*parts) -> str:
    """
    生成缓存键

    Args:
        *parts: 键的各个部分

    Returns:
        str: 拼接后的缓存键
    """
    return ":".join(str(p) for p in parts)


class RedisCache:
    """Redis缓存服务"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        decode_responses: bool = False,
    ):
        """
        初始化Redis缓存

        Args:
            host: Redis主机地址
            port: Redis端口
            db: Redis数据库索引
            password: Redis密码
            decode_responses: 是否解码响应为字符串
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.client = None

        if REDIS_AVAILABLE:
            try:
                self.client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=decode_responses,
                )
                self.client.ping()
                logger.info(f"Redis缓存已连接: {host}:{port}/{db}")
            except Exception as e:
                logger.warning(f"Redis连接失败: {e}")
                self.client = None
        else:
            logger.warning("Redis模块未安装，缓存功能不可用")

    def is_available(self) -> bool:
        """检查Redis是否可用"""
        return REDIS_AVAILABLE and self.client is not None

    def set(self, key: str, value: Any, expire: int = 0) -> bool:
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒），0表示不过期

        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False

        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            if expire > 0:
                self.client.setex(key, expire, serialized_value)
            else:
                self.client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存键

        Returns:
            Any: 缓存值，不存在或出错返回None
        """
        if not self.is_available():
            return None

        try:
            value = self.client.get(key)
            if value is None:
                return None
            if isinstance(value, bytes):
                value = value.decode("utf-8")
            return json.loads(value)
        except Exception as e:
            logger.error(f"获取缓存失败: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False

        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            bool: 是否存在
        """
        if not self.is_available():
            return False

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查缓存存在性失败: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存

        Args:
            pattern: 键模式（支持通配符*）

        Returns:
            int: 清除的键数量
        """
        if not self.is_available():
            return 0

        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return 0

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        增加计数器

        Args:
            key: 缓存键
            amount: 增加量

        Returns:
            int: 增加后的值，失败返回None
        """
        if not self.is_available():
            return None

        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"增加计数器失败: {e}")
            return None

    def expire(self, key: str, seconds: int) -> bool:
        """
        设置键的过期时间

        Args:
            key: 缓存键
            seconds: 过期时间（秒）

        Returns:
            bool: 是否成功
        """
        if not self.is_available():
            return False

        try:
            return self.client.expire(key, seconds)
        except Exception as e:
            logger.error(f"设置过期时间失败: {e}")
            return False


class RedisCacheManager:
    """Redis缓存管理器"""

    @staticmethod
    def clear_project_cache(project_id: Optional[int] = None):
        """清除项目缓存"""
        cache = get_cache()
        if project_id:
            cache.clear_pattern(f"{CacheKeys.PROJECT}:{project_id}*")
        else:
            cache.clear_pattern(f"{CacheKeys.PROJECT}*")

    @staticmethod
    def clear_user_cache(user_id: Optional[int] = None):
        """清除用户缓存"""
        cache = get_cache()
        if user_id:
            cache.clear_pattern(f"{CacheKeys.USER}:{user_id}*")
        else:
            cache.clear_pattern(f"{CacheKeys.USER}*")

    @staticmethod
    def clear_alert_cache():
        """清除告警缓存"""
        cache = get_cache()
        cache.clear_pattern(f"{CacheKeys.ALERT}*")

    @staticmethod
    def clear_search_cache():
        """清除搜索缓存"""
        cache = get_cache()
        cache.clear_pattern(f"{CacheKeys.SEARCH}*")

    @staticmethod
    def clear_dashboard_cache():
        """清除仪表板缓存"""
        cache = get_cache()
        cache.clear_pattern("dashboard*")

    @staticmethod
    def clear_all_cache():
        """清除所有缓存"""
        cache = get_cache()
        if cache.is_available():
            cache.client.flushdb()


# 缓存管理器别名（向后兼容）
CacheManager = RedisCacheManager


# 全局Redis缓存实例
_redis_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """获取全局Redis缓存实例"""
    global _redis_cache_instance
    if _redis_cache_instance is None:
        # 从环境变量读取Redis配置
        import os
        redis_url = os.getenv("REDIS_URL", "")
        
        if redis_url:
            # 解析Redis URL (格式: redis://[:password@]host[:port][/db])
            try:
                from urllib.parse import urlparse
                parsed = urlparse(redis_url)
                _redis_cache_instance = RedisCache(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 6379,
                    db=int(parsed.path.strip("/")) if parsed.path else 0,
                    password=parsed.password,
                )
            except Exception as e:
                logger.warning(f"解析REDIS_URL失败: {e}，使用默认配置")
                _redis_cache_instance = RedisCache()
        else:
            _redis_cache_instance = RedisCache()
    
    return _redis_cache_instance


def cache_result(expire: int = 300):
    """
    缓存装饰器

    Args:
        expire: 缓存过期时间（秒）

    Usage:
        @cache_result(expire=60)
        def get_project(project_id: int):
            return db.query(Project).filter_by(id=project_id).first()
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # 生成缓存键
            import hashlib
            key_str = f"{func.__module__}.{func.__name__}:{args}:{kwargs}"
            key_hash = hashlib.md5(key_str.encode()).hexdigest()
            cache_key_str = f"func:{key_hash}"
            
            # 尝试从缓存获取
            cached = cache.get(cache_key_str)
            if cached is not None:
                return cached
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key_str, result, expire=expire)
            return result
        
        return wrapper
    return decorator
