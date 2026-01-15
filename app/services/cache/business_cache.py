# -*- coding: utf-8 -*-
"""
业务缓存服务

为具体业务场景提供缓存支持
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from app.services.cache.redis_cache import get_cache, cache_key, CacheKeys, cache_result
from app.models.project import Project
from app.models.alert import AlertRecord
from app.models.user import User


class BusinessCacheService:
    """业务缓存服务"""
    
    def __init__(self):
        self.cache = get_cache()
    
    def get_project_list(self, skip: int = 0, limit: int = 50, 
                        status: Optional[str] = None) -> Optional[List[Project]]:
        """
        获取项目列表（带缓存）
        
        缓存策略：
        - 缓存时间：5分钟
        - 键格式：project:list:{skip}:{limit}:{status}
        """
        cache_key = cache_key(CacheKeys.PROJECT_LIST, skip, limit, status or "all")
        
        # 尝试从缓存获取
        cached_projects = self.cache.get(cache_key)
        if cached_projects is not None:
            return cached_projects
        
        return None  # 需要从数据库获取
    
    def set_project_list(self, projects: List[Project], skip: int = 0, 
                         limit: int = 50, status: Optional[str] = None):
        """
        设置项目列表缓存
        """
        cache_key = cache_key(CacheKeys.PROJECT_LIST, skip, limit, status or "all")
        self.cache.set(cache_key, projects, expire=300)  # 5分钟
    
    def get_project_dashboard(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取项目仪表板数据（带缓存）
        
        缓存策略：
        - 缓存时间：2分钟
        - 键格式：project:dashboard:{project_id}
        """
        cache_key = cache_key(CacheKeys.PROJECT_DASHBOARD, project_id)
        return self.cache.get(cache_key)
    
    def set_project_dashboard(self, dashboard_data: Dict[str, Any], project_id: int):
        """
        设置项目仪表板缓存
        """
        cache_key = cache_key(CacheKeys.PROJECT_DASHBOARD, project_id)
        self.cache.set(cache_key, dashboard_data, expire=120)  # 2分钟
    
    def get_alert_statistics(self, days: int = 30) -> Optional[Dict[str, Any]]:
        """
        获取告警统计数据（带缓存）
        
        缓存策略：
        - 缓存时间：10分钟
        - 键格式：alert:stats:{days}
        """
        cache_key = cache_key(CacheKeys.ALERT_STATS, days)
        return self.cache.get(cache_key)
    
    def set_alert_statistics(self, stats: Dict[str, Any], days: int = 30):
        """
        设置告警统计缓存
        """
        cache_key = cache_key(CacheKeys.ALERT_STATS, days)
        self.cache.set(cache_key, stats, expire=600)  # 10分钟
    
    def get_user_permissions(self, user_id: int) -> Optional[List[str]]:
        """
        获取用户权限（带缓存）
        
        缓存策略：
        - 缓存时间：15分钟
        - 键格式：user:permissions:{user_id}
        """
        cache_key = cache_key(CacheKeys.USER_PERMISSIONS, user_id)
        return self.cache.get(cache_key)
    
    def set_user_permissions(self, permissions: List[str], user_id: int):
        """
        设置用户权限缓存
        """
        cache_key = cache_key(CacheKeys.USER_PERMISSIONS, user_id)
        self.cache.set(cache_key, permissions, expire=900)  # 15分钟
    
    def get_search_results(self, search_type: str, keyword: str, 
                          filters: Dict[str, Any]) -> Optional[List[Any]]:
        """
        获取搜索结果（带缓存）
        
        缓存策略：
        - 缓存时间：3分钟
        - 键格式：search:{type}:{keyword}:{filters_hash}
        """
        import hashlib
        filters_str = str(sorted(filters.items()))
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()[:8]
        
        cache_key = cache_key(CacheKeys.SEARCH, search_type, keyword, filters_hash)
        return self.cache.get(cache_key)
    
    def set_search_results(self, results: List[Any], search_type: str, 
                          keyword: str, filters: Dict[str, Any]):
        """
        设置搜索结果缓存
        """
        import hashlib
        filters_str = str(sorted(filters.items()))
        filters_hash = hashlib.md5(filters_str.encode()).hexdigest()[:8]
        
        cache_key = cache_key(CacheKeys.SEARCH, search_type, keyword, filters_hash)
        self.cache.set(cache_key, results, expire=180)  # 3分钟
    
    def get_hot_projects(self, limit: int = 10) -> Optional[List[Project]]:
        """
        获取热门项目（带缓存）
        
        缓存策略：
        - 缓存时间：1小时
        - 键格式：project:hot:{limit}
        """
        cache_key = cache_key(CacheKeys.PROJECT, "hot", limit)
        return self.cache.get(cache_key)
    
    def set_hot_projects(self, projects: List[Project], limit: int = 10):
        """
        设置热门项目缓存
        """
        cache_key = cache_key(CacheKeys.PROJECT, "hot", limit)
        self.cache.set(cache_key, projects, expire=3600)  # 1小时
    
    def get_system_config(self, config_key: str) -> Optional[Any]:
        """
        获取系统配置（带缓存）
        
        缓存策略：
        - 缓存时间：30分钟
        - 键格式：config:{config_key}
        """
        cache_key = cache_key(CacheKeys.CONFIG, config_key)
        return self.cache.get(cache_key)
    
    def set_system_config(self, config_value: Any, config_key: str):
        """
        设置系统配置缓存
        """
        cache_key = cache_key(CacheKeys.CONFIG, config_key)
        self.cache.set(cache_key, config_value, expire=1800)  # 30分钟
    
    def get_project_stats(self, project_id: int) -> Optional[Dict[str, Any]]:
        """
        获取项目统计信息（带缓存）
        
        缓存策略：
        - 缓存时间：5分钟
        - 键格式：project:stats:{project_id}
        """
        cache_key = cache_key(CacheKeys.PROJECT_STATS, project_id)
        return self.cache.get(cache_key)
    
    def set_project_stats(self, stats: Dict[str, Any], project_id: int):
        """
        设置项目统计信息缓存
        """
        cache_key = cache_key(CacheKeys.PROJECT_STATS, project_id)
        self.cache.set(cache_key, stats, expire=300)  # 5分钟
    
    def invalidate_project_cache(self, project_id: int):
        """
        使项目相关缓存失效
        """
        patterns = [
            cache_key(CacheKeys.PROJECT, project_id),
            cache_key(CacheKeys.PROJECT_DASHBOARD, project_id),
            cache_key(CacheKeys.PROJECT_STATS, project_id),
        ]
        
        for pattern in patterns:
            self.cache.delete(pattern)
        
        # 同时清除项目列表缓存（因为项目状态可能已变化）
        self.cache.clear_pattern(f"{CacheKeys.PROJECT_LIST}*")
    
    def invalidate_user_cache(self, user_id: int):
        """
        使用户相关缓存失效
        """
        patterns = [
            cache_key(CacheKeys.USER, user_id),
            cache_key(CacheKeys.USER_PERMISSIONS, user_id),
        ]
        
        for pattern in patterns:
            self.cache.delete(pattern)
    
    def invalidate_alert_cache(self):
        """
        使告警相关缓存失效
        """
        self.cache.clear_pattern(f"{CacheKeys.ALERT}*")
    
    def invalidate_config_cache(self, config_key: Optional[str] = None):
        """
        使配置缓存失效
        """
        if config_key:
            self.cache.delete(cache_key(CacheKeys.CONFIG, config_key))
        else:
            self.cache.clear_pattern(f"{CacheKeys.CONFIG}*")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        """
        if not self.cache.is_available():
            return {"error": "缓存服务不可用"}
        
        try:
            info = self.cache.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": (
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1)
                    * 100
                )
            }
        except Exception as e:
            return {"error": f"获取缓存统计失败: {str(e)}"}


# 全局业务缓存实例
_business_cache_instance: Optional[BusinessCacheService] = None


def get_business_cache() -> BusinessCacheService:
    """获取全局业务缓存实例"""
    global _business_cache_instance
    if _business_cache_instance is None:
        _business_cache_instance = BusinessCacheService()
    return _business_cache_instance


# 便捷的缓存操作函数
def invalidate_cache_on_change(cache_type: str, object_id: Optional[int] = None):
    """
    当数据变更时，使相关缓存失效
    
    Args:
        cache_type: 缓存类型（'project', 'user', 'alert', 'config'）
        object_id: 对象ID（可选）
    """
    business_cache = get_business_cache()
    
    if cache_type == 'project':
        business_cache.invalidate_project_cache(object_id or 0)
    elif cache_type == 'user':
        business_cache.invalidate_user_cache(object_id or 0)
    elif cache_type == 'alert':
        business_cache.invalidate_alert_cache()
    elif cache_type == 'config':
        business_cache.invalidate_config_cache(str(object_id) if object_id else None)