# -*- coding: utf-8 -*-
"""
缓存服务
提供通用的缓存功能，支持 TTL 和手动失效
"""

import time
from typing import Any, Dict, Optional, Set, List
from functools import lru_cache
from threading import Lock


class CacheService:
    """
    通用缓存服务
    
    支持的缓存类型：
    - 内存缓存（本模块实现）
    - LRU 缓存（使用 functools.lru_cache）
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._memory_cache: Dict[str, Dict[str, Any]] = {}
        return cls._instance
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            default: 默认值（缓存不存在时返回）
            
        Returns:
            缓存值或默认值
        """
        cached = self._memory_cache.get(key)
        if cached:
            # 检查是否过期
            if time.time() < cached['expiry']:
                return cached['value']
            else:
                # 过期删除
                del self._memory_cache[key]
        return default
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒），默认 300 秒
        """
        self._memory_cache[key] = {
            'value': value,
            'expiry': time.time() + ttl,
        }
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if key in self._memory_cache:
            del self._memory_cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        self._memory_cache.clear()
    
    def clear_prefix(self, prefix: str) -> int:
        """
        清除指定前缀的所有缓存
        
        Args:
            prefix: 缓存键前缀
            
        Returns:
            清除的缓存数量
        """
        keys_to_delete = [k for k in self._memory_cache.keys() if k.startswith(prefix)]
        for key in keys_to_delete:
            del self._memory_cache[key]
        return len(keys_to_delete)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        total_keys = len(self._memory_cache)
        expired_keys = sum(
            1 for cached in self._memory_cache.values()
            if time.time() >= cached['expiry']
        )
        valid_keys = total_keys - expired_keys
        
        return {
            'total_keys': total_keys,
            'valid_keys': valid_keys,
            'expired_keys': expired_keys,
            'memory_usage_mb': len(str(self._memory_cache)) / (1024 * 1024),
        }


class DepartmentCache:
    """部门ID缓存（优化 DataScopeService 性能）"""
    
    _cache: Dict[str, int] = {}
    _lock = Lock()
    _default_ttl = 3600  # 1 小时
    
    @classmethod
    def get(cls, dept_name: str) -> Optional[int]:
        """
        获取部门ID
        
        Args:
            dept_name: 部门名称
            
        Returns:
            部门ID，如果不存在返回 None
        """
        return cls._cache.get(dept_name)
    
    @classmethod
    def set(cls, dept_name: str, dept_id: int) -> None:
        """
        设置部门ID缓存
        
        Args:
            dept_name: 部门名称
            dept_id: 部门ID
        """
        with cls._lock:
            cls._cache[dept_name] = dept_id
    
    @classmethod
    def delete(cls, dept_name: str) -> None:
        """
        删除部门ID缓存
        
        Args:
            dept_name: 部门名称
        """
        with cls._lock:
            if dept_name in cls._cache:
                del cls._cache[dept_name]
    
    @classmethod
    def clear(cls) -> None:
        """清空所有部门缓存"""
        with cls._lock:
            cls._cache.clear()
    
    @classmethod
    def get_size(cls) -> int:
        """
        获取缓存大小
        
        Returns:
            缓存的部门数量
        """
        return len(cls._cache)


class UserProjectCache:
    """
    用户项目缓存
    
    缓存用户参与的项目列表，减少频繁的数据库查询
    """
    
    _cache: Dict[int, Dict[str, Any]] = {}
    _lock = Lock()
    _default_ttl = 300  # 5 分钟
    
    @classmethod
    def get(cls, user_id: int) -> Optional[Set[int]]:
        """
        获取用户的项目ID列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            项目ID集合，如果不存在或已过期返回 None
        """
        cached = cls._cache.get(user_id)
        if cached:
            # 检查是否过期
            if time.time() < cached['expiry']:
                return cached['project_ids']
            else:
                # 过期删除
                with cls._lock:
                    if user_id in cls._cache:
                        del cls._cache[user_id]
        return None
    
    @classmethod
    def set(cls, user_id: int, project_ids: Set[int], ttl: int = None) -> None:
        """
        设置用户的项目ID列表缓存
        
        Args:
            user_id: 用户ID
            project_ids: 项目ID集合
            ttl: 生存时间（秒），默认使用 _default_ttl
        """
        if ttl is None:
            ttl = cls._default_ttl
        
        with cls._lock:
            cls._cache[user_id] = {
                'project_ids': project_ids,
                'expiry': time.time() + ttl,
            }
    
    @classmethod
    def delete(cls, user_id: int) -> None:
        """
        删除用户的项目缓存
        
        Args:
            user_id: 用户ID
        """
        with cls._lock:
            if user_id in cls._cache:
                del cls._cache[user_id]
    
    @classmethod
    def clear(cls) -> None:
        """清空所有用户项目缓存"""
        with cls._lock:
            cls._cache.clear()
    
    @classmethod
    def clear_by_project(cls, project_id: int) -> int:
        """
        清除包含指定项目的所有用户缓存
        
        Args:
            project_id: 项目ID
            
        Returns:
            清除的缓存数量
        """
        with cls._lock:
            keys_to_delete = [
                user_id for user_id, cached in cls._cache.items()
                if project_id in cached.get('project_ids', set())
            ]
            for user_id in keys_to_delete:
                del cls._cache[user_id]
            return len(keys_to_delete)
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        total_users = len(cls._cache)
        expired_users = sum(
            1 for cached in cls._cache.values()
            if time.time() >= cached['expiry']
        )
        valid_users = total_users - expired_users
        
        total_projects = sum(
            len(cached.get('project_ids', set()))
            for cached in cls._cache.values()
        )
        
        return {
            'total_users': total_users,
            'valid_users': valid_users,
            'expired_users': expired_users,
            'total_projects': total_projects,
        }


class UserPermissionCache:
    """
    用户权限缓存
    
    缓存用户的权限列表，减少频繁的数据库查询
    """
    
    _default_ttl = 600  # 10 分钟
    
    @staticmethod
    @lru_cache(maxsize=1000)
    def get_user_permissions(user_id: int) -> Set[str]:
        """
        获取用户权限集合（带 LRU 缓存）
        
        注意：这是一个装饰器缓存，需要手动失效
        
        Args:
            user_id: 用户ID
            
        Returns:
            权限编码集合
        """
        # 这里应该从数据库查询
        # 实际实现在 service 层
        return set()
    
    @classmethod
    def invalidate_user(cls, user_id: int) -> None:
        """
        使指定用户的缓存失效
        
        Args:
            user_id: 用户ID
        """
        # 清除 lru_cache
        if hasattr(cls.get_user_permissions, 'cache_clear'):
            # lru_cache 无法针对特定 key 失效
            # 只能全部清除
            cls.get_user_permissions.cache_clear()
    
    @classmethod
    def invalidate_all(cls) -> None:
        """使所有缓存失效"""
        if hasattr(cls.get_user_permissions, 'cache_clear'):
            cls.get_user_permissions.cache_clear()
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        cache_info = getattr(cls.get_user_permissions, 'cache_info', None)
        if cache_info:
            return {
                'hits': cache_info.hits,
                'misses': cache_info.misses,
                'maxsize': cache_info.maxsize,
                'currsize': cache_info.currsize,
            }
        return {
            'hits': 0,
            'misses': 0,
            'maxsize': 0,
            'currsize': 0,
        }
