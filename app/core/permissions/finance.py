# -*- coding: utf-8 -*-
"""
权限检查模块 - 财务权限
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.user import User


def has_finance_access(user: User) -> bool:
    """
    检查用户是否有财务管理模块的访问权限

    注意：此配置需要与前端 frontend/src/lib/roleConfig.js 中的 hasFinanceAccess() 保持同步
    当修改前端权限时，请同步更新此函数
    """
    if user.is_superuser:
        return True

    # 定义有财务权限的角色代码
    # 与前端 frontend/src/lib/roleConfig.js 中的 hasFinanceAccess() 保持一致
    finance_roles = [
        # 管理层
        "admin",
        "super_admin",
        "chairman",
        "gm",
        "管理员",
        "系统管理员",
        "董事长",
        "总经理",
        # 财务部门
        "finance_manager",
        "finance",
        "accountant",
        "财务经理",
        "财务人员",
        "会计",
        # 销售部门（需要访问回款监控）
        "sales_director",
        "sales_manager",
        "sales",
        "销售总监",
        "销售经理",
        "销售工程师",
        "business_support",
        "presales_manager",
        "presales",
        "商务支持",
        "商务支持专员",
        "售前经理",
        "售前技术工程师",
        # 项目管理部门（需要查看项目回款情况）
        "project_dept_manager",
        "pmc",
        "pm",
        "项目部经理",
        "项目经理",
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        # 同时检查英文和中文角色名
        role_name = user_role.role.role_name if user_role.role.role_name else ""
        if role_code in finance_roles or role_name in finance_roles:
            return True

    return False


def require_finance_access():
    """财务权限检查依赖"""

    async def finance_checker(current_user: User = Depends(get_current_active_user)):
        if not has_finance_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问财务管理模块",
            )
        return current_user

    return finance_checker
