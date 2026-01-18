# -*- coding: utf-8 -*-
"""
权限检查模块 - 生产权限
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.user import User


def has_production_access(user: User) -> bool:
    """检查用户是否有生产管理模块的访问权限"""
    if user.is_superuser:
        return True

    # 定义有生产权限的角色代码
    production_roles = [
        "production_manager",
        "manufacturing_director",
        "生产部经理",
        "制造总监",
        "pmc",
        "pmo_dir",  # 项目管理部总监（生产进度查看）
        "项目管理部总监",
        "me_mgr",  # 机械部经理
        "机械部经理",
        "ee_mgr",  # 电气部经理
        "电气部经理",
        "assembler",
        "assembler_mechanic",
        "assembler_electrician",
        "装配技工",
        "装配钳工",
        "装配电工",
        "gm",
        "总经理",
        "chairman",
        "董事长",
        "admin",
        "super_admin",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        if role_code in production_roles:
            return True

    return False


def require_production_access():
    """生产权限检查依赖"""

    async def production_checker(current_user: User = Depends(get_current_active_user)):
        if not has_production_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问生产管理模块",
            )
        return current_user

    return production_checker
