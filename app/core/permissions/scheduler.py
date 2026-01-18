# -*- coding: utf-8 -*-
"""
权限检查模块 - 调度器管理权限
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.user import User


def has_scheduler_admin_access(user: User) -> bool:
    """
    检查用户是否有调度器管理权限

    调度器管理权限包括：手动触发任务、更新任务配置、同步任务配置
    只有管理员和系统管理员可以操作

    Args:
        user: 当前用户

    Returns:
        bool: 是否有调度器管理权限
    """
    if user.is_superuser:
        return True

    # 定义有调度器管理权限的角色代码
    admin_roles = [
        "admin",  # 管理员
        "super_admin",  # 超级管理员
        "系统管理员",
        "管理员",
        "gm",  # 总经理
        "总经理",
        "chairman",  # 董事长
        "董事长",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in admin_roles or role_name in admin_roles:
            return True

    return False


def require_scheduler_admin_access():
    """调度器管理权限检查依赖"""

    async def admin_checker(current_user: User = Depends(get_current_active_user)):
        if not has_scheduler_admin_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理调度器，仅管理员可以操作",
            )
        return current_user

    return admin_checker
