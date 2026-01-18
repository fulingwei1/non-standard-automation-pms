# -*- coding: utf-8 -*-
"""
权限检查模块 - 研发项目权限
"""

from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.user import User

# 研发项目角色列表
RD_PROJECT_ROLES = [
    "admin",
    "super_admin",
    "管理员",
    "系统管理员",
    "tech_dev_manager",
    "技术开发部经理",
    "rd_engineer",
    "研发工程师",
    "me_engineer",
    "机械工程师",
    "me_mgr",  # 机械部经理
    "机械部经理",
    "ee_engineer",
    "电气工程师",
    "ee_mgr",  # 电气部经理
    "电气部经理",
    "sw_engineer",
    "软件工程师",
    "te_engineer",
    "测试工程师",
    "me_dept_manager",
    "机械部经理",
    "ee_dept_manager",
    "电气部经理",
    "te_dept_manager",
    "测试部经理",
    "project_dept_manager",
    "项目部经理",
    "pmo_dir",  # 项目管理部总监
    "项目管理部总监",
    "pm",
    "pmc",
    "项目经理",
    "gm",
    "总经理",
    "chairman",
    "董事长",
]


def has_rd_project_access(user: User) -> bool:
    """检查用户是否有研发项目访问权限"""
    if user.is_superuser:
        return True
    
    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in RD_PROJECT_ROLES or role_name in RD_PROJECT_ROLES:
            return True
    
    return False


def require_rd_project_access():
    """研发项目权限检查依赖"""

    async def rd_project_checker(current_user: User = Depends(get_current_active_user)):
        if not has_rd_project_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问研发项目管理功能",
            )
        return current_user

    return rd_project_checker
