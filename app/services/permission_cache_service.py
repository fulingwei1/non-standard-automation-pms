# -*- coding: utf-8 -*-
"""
权限缓存服务 - 重新导出模块

此模块重新导出 permission_management 模块中的权限缓存服务，
用于向后兼容。实际实现在 app/services/permission_management/permission_cache_service.py
"""

from app.services.cache_service import CacheService
from app.services.permission_management import permission_cache_service as _impl
from app.services.permission_management.permission_cache_service import (
    CACHE_PREFIX_ROLE_PERMISSIONS,
    CACHE_PREFIX_ROLE_USERS,
    CACHE_PREFIX_TENANT,
    CACHE_PREFIX_USER_PERMISSIONS,
    CACHE_PREFIX_USER_ROLES,
    PERMISSION_CACHE_TTL,
    ROLE_CACHE_TTL,
)


class PermissionCacheService(_impl.PermissionCacheService):
    """兼容旧导入路径，并允许旧测试 patch 本模块的 CacheService。"""

    def __init__(self):
        _impl.CacheService = CacheService
        super().__init__()


def get_permission_cache_service() -> PermissionCacheService:
    """获取兼容路径下的权限缓存服务单例。"""
    if _impl._permission_cache_service is None or not isinstance(
        _impl._permission_cache_service, PermissionCacheService
    ):
        _impl.CacheService = CacheService
        _impl._permission_cache_service = PermissionCacheService()
    return _impl._permission_cache_service

__all__ = [
    "PermissionCacheService",
    "get_permission_cache_service",
    "CacheService",
    "CACHE_PREFIX_USER_PERMISSIONS",
    "CACHE_PREFIX_ROLE_PERMISSIONS",
    "CACHE_PREFIX_USER_ROLES",
    "CACHE_PREFIX_ROLE_USERS",
    "CACHE_PREFIX_TENANT",
    "PERMISSION_CACHE_TTL",
    "ROLE_CACHE_TTL",
]
