# -*- coding: utf-8 -*-
"""
权限缓存服务 - 重新导出模块

此模块重新导出 permission_management 模块中的权限缓存服务，
用于向后兼容。实际实现在 app/services/permission_management/permission_cache_service.py
"""

from app.services.permission_management.permission_cache_service import (
    PermissionCacheService,
    get_permission_cache_service,
    CACHE_PREFIX_USER_PERMISSIONS,
    CACHE_PREFIX_ROLE_PERMISSIONS,
    CACHE_PREFIX_USER_ROLES,
    CACHE_PREFIX_ROLE_USERS,
    CACHE_PREFIX_TENANT,
    PERMISSION_CACHE_TTL,
    ROLE_CACHE_TTL,
)

__all__ = [
    "PermissionCacheService",
    "get_permission_cache_service",
    "CACHE_PREFIX_USER_PERMISSIONS",
    "CACHE_PREFIX_ROLE_PERMISSIONS",
    "CACHE_PREFIX_USER_ROLES",
    "CACHE_PREFIX_ROLE_USERS",
    "CACHE_PREFIX_TENANT",
    "PERMISSION_CACHE_TTL",
    "ROLE_CACHE_TTL",
]