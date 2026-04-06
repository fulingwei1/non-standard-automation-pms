# -*- coding: utf-8 -*-
"""
权限审计服务 - 重新导出模块

此模块重新导出 permission_management 模块中的权限审计服务，
用于向后兼容。实际实现在 app/services/permission_management/permission_audit_service.py
"""

from app.services.permission_management.permission_audit_service import (
    PermissionAuditService,
    get_permission_audit_service,
)

__all__ = [
    "PermissionAuditService",
    "get_permission_audit_service",
]