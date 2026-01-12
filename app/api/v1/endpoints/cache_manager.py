# -*- coding: utf-8 -*-
"""
缓存管理工具 - 统一的缓存失效逻辑
"""

from typing import Optional
from sqlalchemy.orm import Session

from app.services.cache_service import CacheService

# 全局缓存服务实例
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """获取缓存服务实例（单例）"""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


class ProjectCacheInvalidator:
    """项目缓存失效器"""

    @staticmethod
    def invalidate_project(project_id: int) -> None:
        """
        使项目相关的所有缓存失效

        Args:
            project_id: 项目ID
        """
        cache_service = get_cache_service()
        try:
            # 失效项目详情缓存
            cache_service.invalidate_project_detail(project_id)
            # 失效项目列表缓存
            cache_service.invalidate_project_list()
            # 失效项目统计缓存
            cache_service.invalidate_project_statistics()
        except Exception:
            # 缓存失效失败不影响主流程
            pass

    @staticmethod
    def invalidate_project_list() -> None:
        """使所有项目列表缓存失效"""
        cache_service = get_cache_service()
        try:
            cache_service.invalidate_project_list()
        except Exception:
            pass

    @staticmethod
    def invalidate_project_statistics() -> None:
        """使所有项目统计缓存失效"""
        cache_service = get_cache_service()
        try:
            cache_service.invalidate_project_statistics()
        except Exception:
            pass

    @staticmethod
    def invalidate_all() -> None:
        """使所有项目相关缓存失效"""
        cache_service = get_cache_service()
        try:
            cache_service.invalidate_all_project_cache()
        except Exception:
            pass


def invalidate_on_project_update(func):
    """
    项目更新操作的缓存失效装饰器

    Usage:
        @invalidate_on_project_update
        def update_project(project_id: int, data: dict):
            # 更新逻辑
            pass
    """
    def wrapper(*args, **kwargs):
        # 执行原始函数
        result = func(*args, **kwargs)

        # 提取project_id
        project_id = kwargs.get('project_id') or (args[1] if len(args) > 1 else None)

        # 失效缓存
        if project_id:
            ProjectCacheInvalidator.invalidate_project(project_id)

        return result

    return wrapper


def invalidate_on_project_list_change(func):
    """
    项目列表变更操作的缓存失效装饰器

    Usage:
        @invalidate_on_project_list_change
        def create_project(data: dict):
            # 创建逻辑
            pass
    """
    def wrapper(*args, **kwargs):
        # 执行原始函数
        result = func(*args, **kwargs)

        # 失效列表缓存
        ProjectCacheInvalidator.invalidate_project_list()
        ProjectCacheInvalidator.invalidate_project_statistics()

        return result

    return wrapper
