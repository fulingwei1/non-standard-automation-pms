# -*- coding: utf-8 -*-
"""
权限检查模块 - 采购权限
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.user import User


def has_procurement_access(user: User) -> bool:
    """检查用户是否有采购和物料管理模块的访问权限"""
    if user.is_superuser:
        return True

    # 定义有采购权限的角色代码
    procurement_roles = [
        "procurement_engineer",
        "procurement_manager",
        "procurement",
        "buyer",
        "pmc",
        "production_manager",
        "manufacturing_director",
        "pmo_dir",  # 项目管理部总监（项目物料查看）
        "gm",
        "chairman",
        "admin",
        "super_admin",
        "pm",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        if role_code in procurement_roles:
            return True

    return False


def require_procurement_access():
    """采购权限检查依赖"""

    async def procurement_checker(
        current_user: User = Depends(get_current_active_user),
    ):
        if not has_procurement_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问采购和物料管理模块",
            )
        return current_user

    return procurement_checker


def has_shortage_report_access(user: User) -> bool:
    """检查用户是否有缺料上报权限"""
    if user.is_superuser:
        return True

    # 定义有缺料上报权限的角色代码
    shortage_report_roles = [
        # 生产一线人员
        "assembler",  # 装配技工
        "assembler_mechanic",  # 装配钳工
        "assembler_electrician",  # 装配电工
        # 仓库管理人员
        "warehouse",  # 仓库管理员
        # 计划管理人员
        "pmc",  # PMC计划员
        # 车间管理人员（可根据实际情况调整）
        "production_manager",  # 生产部经理
        "manufacturing_director",  # 制造总监
        # 管理层
        "gm",  # 总经理
        "chairman",  # 董事长
        "admin",  # 系统管理员
        "super_admin",  # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        if role_code in shortage_report_roles:
            return True

    return False


def require_shortage_report_access():
    """缺料上报权限检查依赖"""

    async def shortage_report_checker(
        current_user: User = Depends(get_current_active_user),
    ):
        if not has_shortage_report_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行缺料上报，只有生产人员、仓管、PMC等角色可以上报缺料",
            )
        return current_user

    return shortage_report_checker
