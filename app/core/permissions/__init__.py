# -*- coding: utf-8 -*-
"""
权限模块 - 保留工时相关业务逻辑函数

注意：简单的权限检查已迁移到数据库驱动模式。
使用 require_permission("module:action") 代替旧的 require_*_access() 函数。

此模块仅保留工时模块的复杂业务逻辑函数。
"""

from .timesheet import (
    apply_timesheet_access_filter,
    check_bulk_timesheet_approval_permission,
    check_timesheet_approval_permission,
    get_user_manageable_dimensions,
    has_timesheet_approval_access,
    is_timesheet_admin,
    require_timesheet_approval_access,
)

__all__ = [
    "is_timesheet_admin",
    "get_user_manageable_dimensions",
    "apply_timesheet_access_filter",
    "check_timesheet_approval_permission",
    "check_bulk_timesheet_approval_permission",
    "has_timesheet_approval_access",
    "require_timesheet_approval_access",
]
