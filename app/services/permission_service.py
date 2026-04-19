# -*- coding: utf-8 -*-
"""
权限服务 - 重新导出模块

此模块重新导出 permission_management 模块中的权限服务，
用于向后兼容。实际实现在 app/services/permission_management/permission_service.py
"""

from app.services.permission_management.permission_cache_service import get_permission_cache_service
from app.services.permission_management.permission_service import (
    PermissionService,
    check_permission_compat,
    has_module_permission,
)

__all__ = [
    "PermissionService",
    "check_permission_compat",
    "has_module_permission",
]