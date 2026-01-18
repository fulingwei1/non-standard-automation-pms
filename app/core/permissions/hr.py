# -*- coding: utf-8 -*-
"""
权限检查模块 - 人力资源权限
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.user import User


def has_hr_access(user: User) -> bool:
    """检查用户是否有人力资源管理模块的访问权限（奖金规则配置等）"""
    if user.is_superuser:
        return True

    # 定义有人力资源权限的角色代码
    hr_roles = [
        "hr_manager",  # 人力资源经理
        "人事经理",
        "hr",  # 人力资源专员
        "人事",
        "gm",  # 总经理
        "总经理",
        "chairman",  # 董事长
        "董事长",
        "admin",  # 系统管理员
        "super_admin",  # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in hr_roles or role_name in hr_roles:
            return True

    return False


def require_hr_access():
    """人力资源权限检查依赖"""

    async def hr_checker(current_user: User = Depends(get_current_active_user)):
        if not has_hr_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问人力资源配置功能，仅人力资源经理可以配置",
            )
        return current_user

    return hr_checker
