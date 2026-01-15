# -*- coding: utf-8 -*-
"""
Redis缓存服务

为热点数据提供缓存支持，提升系统性能
"""

import json
import pickle
import logging
from typing import Any, Optional, Union, List
from datetime import timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None,
                 decode_responses: bool = False):
        """
        初始化Redis连接
        
        Args:
            host: Redis主机地址
            port: Redis端口
            db: 数据库编号
            password: 密码
            decode_responses: 是否解码响应
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.decode_responses = decode_responses
        self.client = None
        
        if REDIS_AVAILABLE:
            self._connect()
        else:
            logger.warning("Redis未安装，缓存功能将被禁用")
    
    def _connect(self):
        """建立Redis连接"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=self.decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # 测试连接
            self.client.ping()
            logger.info(f"Redis连接成功: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Redis连接失败: {str(e)}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not REDIS_AVAILABLE or not self.client:
            return False
        
        try:
            self.client.ping()
            return True
        except:
            return False
    
    def set(self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            expire: 过期时间（秒）或timedelta对象
            
        Returns:
            bool: 设置是否成功
        """
        if not self.is_available():
            return False
        
        try:
            if self.decode_responses:
                # 如果decode_responses=True，只能存储字符串
                serialized_value = json.dumps(value, ensure_ascii=False, default=str)
            else:
                # 使用pickle序列化复杂对象
                serialized_value = pickle.dumps(value)
            
            return self.client.set(key, serialized_value, ex=expire)
        except Exception as e:
            logger.error(f"缓存设置失败 {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
            
        Returns:
            Any: 缓存值，如果不存在则返回None
        """
        if not self.is_available():
            return None
        
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            if self.decode_responses:
                # JSON反序列化
                return json.loads(value)
            else:
                # pickle反序列化
                return pickle.loads(value)
        except Exception as e:
            logger.error(f"缓存获取失败 {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 删除是否成功
        """
        if not self.is_available():
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"缓存删除失败 {key}: {str(e)}")
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
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"缓存检查失败 {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存
        
        Args:
            pattern: 匹配模式（如 "user:*"）
            
        Returns:
            int: 删除的键数量
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"批量清除缓存失败 {pattern}: {str(e)}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        递增缓存值
        
        Args:
            key: 缓存键
            amount: 递增量
            
        Returns:
            int: 递增后的值
        """
        if not self.is_available():
            return None
        
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"缓存递增失败 {key}: {str(e)}")
            return None
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        设置缓存过期时间
        
        Args:
            key: 缓存键
            seconds: 过期时间（秒）
            
        Returns:
            bool: 设置是否成功
        """
        if not self.is_available():
            return False
        
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"设置过期时间失败 {key}: {str(e)}")
            return False


# 全局缓存实例
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """获取全局缓存实例"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def cache_key(*parts) -> str:
    """生成缓存键"""
    return ":".join(str(part) for part in parts)


# 常用缓存键前缀
class CacheKeys:
    """缓存键常量"""
    
    PROJECT = "project"
    PROJECT_LIST = "project:list"
    PROJECT_DASHBOARD = "project:dashboard"
    PROJECT_STATS = "project:stats"
    
    USER = "user"
    USER_SESSION = "user:session"
    USER_PERMISSIONS = "user:permissions"
    
    ALERT = "alert"
    ALERT_STATS = "alert:stats"
    
    SHORTAGE = "shortage"
    SHORTAGE_STATS = "shortage:stats"
    
    CONTRACT = "contract"
    CONTRACT_STATS = "contract:stats"
    
    CONFIG = "config"
    DICTIONARY = "dictionary"
    
    SEARCH = "search"
    DASHBOARD = "dashboard"


# 缓存装饰器
def cache_result(key_prefix: str, expire: Union[int, timedelta] = 300):
    """
    缓存函数结果装饰器
    
    Args:
        key_prefix: 缓存键前缀
        expire: 过期时间（秒）
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key_str = cache_key(key_prefix, str(args), str(kwargs))
            cache = get_cache()
            
            # 尝试从缓存获取
            cached_result = cache.get(cache_key_str)
            if cached_result is not None:
                return cached_result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.set(cache_key_str, result, expire=expire)
            
            return result
        
        return wrapper
    return decorator


# 缓存管理工具
class CacheManager:
    """缓存管理工具"""
    
    @staticmethod
    def clear_project_cache(project_id: Optional[int] = None):
        """清除项目相关缓存"""
        cache = get_cache()
        
        if project_id:
            # 清除特定项目的缓存
            patterns = [
                f"{CacheKeys.PROJECT}:{project_id}*",
                f"{CacheKeys.PROJECT_DASHBOARD}:{project_id}",
                f"{CacheKeys.PROJECT_STATS}:{project_id}",
            ]
        else:
            # 清除所有项目缓存
            patterns = [
                f"{CacheKeys.PROJECT}*",
                f"{CacheKeys.PROJECT_LIST}*",
                f"{CacheKeys.PROJECT_DASHBOARD}*",
                f"{CacheKeys.PROJECT_STATS}*",
            ]
        
        for pattern in patterns:
            cache.clear_pattern(pattern)
    
    @staticmethod
    def clear_user_cache(user_id: Optional[int] = None):
        """清除用户相关缓存"""
        cache = get_cache()
        
        if user_id:
            patterns = [
                f"{CacheKeys.USER}:{user_id}*",
                f"{CacheKeys.USER_SESSION}:{user_id}*",
                f"{CacheKeys.USER_PERMISSIONS}:{user_id}*",
            ]
        else:
            patterns = [
                f"{CacheKeys.USER}*",
                f"{CacheKeys.USER_SESSION}*",
                f"{CacheKeys.USER_PERMISSIONS}*",
            ]
        
        for pattern in patterns:
            cache.clear_pattern(pattern)
    
    @staticmethod
    def clear_alert_cache():
        """清除告警相关缓存"""
        cache = get_cache()
        
        patterns = [
            f"{CacheKeys.ALERT}*",
            f"{CacheKeys.ALERT_STATS}*",
        ]
        
        for pattern in patterns:
            cache.clear_pattern(pattern)
    
    @staticmethod
    def clear_search_cache():
        """清除搜索缓存"""
        cache = get_cache()
        cache.clear_pattern(f"{CacheKeys.SEARCH}*")
    
    @staticmethod
    def clear_dashboard_cache():
        """清除仪表板缓存"""
        cache = get_cache()
        cache.clear_pattern(f"{CacheKeys.DASHBOARD}*")
    
    @staticmethod
    def clear_all_cache():
        """清除所有缓存"""
        cache = get_cache()
        if cache.is_available():
            cache.client.flushdb()
            logger.info("所有缓存已清除")