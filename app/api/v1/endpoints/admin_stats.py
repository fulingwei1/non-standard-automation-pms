# -*- coding: utf-8 -*-
"""
管理员驾驶台统计 API
提供用户、角色、权限等系统统计数据
"""
from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.core import security
from app.models.user import User, Role, Permission, UserRole, RolePermission
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/admin/stats", response_model=ResponseModel)
def get_admin_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取管理员驾驶台统计数据

    返回用户、角色、权限等统计信息
    """
    # 用户统计
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    inactive_users = total_users - active_users

    # 有角色的用户数
    users_with_roles = db.query(func.count(func.distinct(UserRole.user_id))).scalar() or 0
    users_without_roles = total_users - users_with_roles

    # 角色统计
    total_roles = db.query(func.count(Role.id)).scalar() or 0
    active_roles = db.query(func.count(Role.id)).filter(Role.is_active == True).scalar() or 0
    inactive_roles = total_roles - active_roles

    # 系统角色 vs 自定义角色（假设系统角色是 is_system = True 或按某种规则区分）
    # 如果没有 is_system 字段，可以按其他方式区分，这里简单处理
    system_roles = db.query(func.count(Role.id)).filter(Role.role_code.in_([
        'admin', 'gm', 'vp', 'chairman', 'employee'
    ])).scalar() or 0
    custom_roles = total_roles - system_roles

    # 权限统计
    total_permissions = db.query(func.count(Permission.id)).scalar() or 0

    # 已分配的权限数（角色-权限关联总数）
    assigned_permissions = db.query(func.count(RolePermission.id)).scalar() or 0

    # 未分配给任何角色的权限数
    assigned_perm_ids = db.query(RolePermission.permission_id).distinct().subquery()
    unassigned_permissions = db.query(func.count(Permission.id)).filter(
        ~Permission.id.in_(assigned_perm_ids)
    ).scalar() or 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            # 用户统计
            "totalUsers": total_users,
            "activeUsers": active_users,
            "inactiveUsers": inactive_users,
            "usersWithRoles": users_with_roles,
            "usersWithoutRoles": users_without_roles,
            "newUsersThisMonth": 0,  # 可后续实现

            # 角色统计
            "totalRoles": total_roles,
            "systemRoles": system_roles,
            "customRoles": custom_roles,
            "activeRoles": active_roles,
            "inactiveRoles": inactive_roles,

            # 权限统计
            "totalPermissions": total_permissions,
            "assignedPermissions": assigned_permissions,
            "unassignedPermissions": unassigned_permissions,

            # 系统健康（简化版本，可后续扩展）
            "systemUptime": 99.9,
            "databaseSize": 0,  # 可后续实现
            "storageUsed": 0,  # 可后续实现
            "apiResponseTime": 0,  # 可后续实现
            "errorRate": 0,  # 可后续实现

            # 活动统计（可后续实现）
            "loginCountToday": 0,
            "loginCountThisWeek": 0,
            "lastBackup": None,
            "auditLogsToday": 0,
            "auditLogsThisWeek": 0,
        }
    )
