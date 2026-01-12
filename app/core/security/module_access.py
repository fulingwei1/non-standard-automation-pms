# -*- coding: utf-8 -*-
"""
模块访问权限

包含采购、财务、生产、HR、调度器等模块的访问权限检查
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.user import User
from .deps import get_current_active_user


def has_procurement_access(user: User) -> bool:
    """检查用户是否有采购和物料管理模块的访问权限"""
    if user.is_superuser:
        return True

    # 定义有采购权限的角色代码
    procurement_roles = [
        'procurement_engineer',
        'procurement_manager',
        'procurement',
        'buyer',
        'pmc',
        'production_manager',
        'manufacturing_director',
        'gm',
        'chairman',
        'admin',
        'super_admin',
        'pm',
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in procurement_roles:
            return True

    return False


def require_procurement_access():
    """采购权限检查依赖"""
    async def procurement_checker(current_user: User = Depends(get_current_active_user)):
        if not has_procurement_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问采购和物料管理模块"
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
        'assembler',              # 装配技工
        'assembler_mechanic',     # 装配钳工
        'assembler_electrician',  # 装配电工
        # 仓库管理人员
        'warehouse',              # 仓库管理员
        # 计划管理人员
        'pmc',                    # PMC计划员
        # 车间管理人员（可根据实际情况调整）
        'production_manager',     # 生产部经理
        'manufacturing_director', # 制造总监
        # 管理层
        'gm',                     # 总经理
        'chairman',               # 董事长
        'admin',                  # 系统管理员
        'super_admin',            # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in shortage_report_roles:
            return True

    return False


def require_shortage_report_access():
    """缺料上报权限检查依赖"""
    async def shortage_report_checker(current_user: User = Depends(get_current_active_user)):
        if not has_shortage_report_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行缺料上报，只有生产人员、仓管、PMC等角色可以上报缺料"
            )
        return current_user
    return shortage_report_checker


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
        'admin', 'super_admin', 'chairman', 'gm',
        '管理员', '系统管理员', '董事长', '总经理',
        # 财务部门
        'finance_manager', 'finance', 'accountant',
        '财务经理', '财务人员', '会计',
        # 销售部门（需要访问回款监控）
        'sales_director', 'sales_manager', 'sales',
        '销售总监', '销售经理', '销售工程师',
        'business_support', 'presales_manager', 'presales',
        '商务支持', '商务支持专员', '售前经理', '售前技术工程师',
        # 项目管理部门（需要查看项目回款情况）
        'project_dept_manager', 'pmc', 'pm',
        '项目部经理', '项目经理',
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        # 同时检查英文和中文角色名
        role_name = user_role.role.role_name if user_role.role.role_name else ''
        if role_code in finance_roles or role_name in finance_roles:
            return True

    return False


def require_finance_access():
    """财务权限检查依赖"""
    async def finance_checker(current_user: User = Depends(get_current_active_user)):
        if not has_finance_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问财务管理模块"
            )
        return current_user
    return finance_checker


def has_production_access(user: User) -> bool:
    """检查用户是否有生产管理模块的访问权限"""
    if user.is_superuser:
        return True

    # 定义有生产权限的角色代码
    production_roles = [
        'production_manager',
        'manufacturing_director',
        '生产部经理',
        '制造总监',
        'pmc',
        'assembler',
        'assembler_mechanic',
        'assembler_electrician',
        '装配技工',
        '装配钳工',
        '装配电工',
        'gm',
        '总经理',
        'chairman',
        '董事长',
        'admin',
        'super_admin',
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in production_roles:
            return True

    return False


def require_production_access():
    """生产权限检查依赖"""
    async def production_checker(current_user: User = Depends(get_current_active_user)):
        if not has_production_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问生产管理模块"
            )
        return current_user
    return production_checker


def has_hr_access(user: User) -> bool:
    """检查用户是否有人力资源管理模块的访问权限（奖金规则配置等）"""
    if user.is_superuser:
        return True

    # 定义有人力资源权限的角色代码
    hr_roles = [
        'hr_manager',           # 人力资源经理
        '人事经理',
        'hr',                   # 人力资源专员
        '人事',
        'gm',                   # 总经理
        '总经理',
        'chairman',             # 董事长
        '董事长',
        'admin',                # 系统管理员
        'super_admin',          # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in hr_roles or role_name in hr_roles:
            return True

    return False


def require_hr_access():
    """人力资源权限检查依赖"""
    async def hr_checker(current_user: User = Depends(get_current_active_user)):
        if not has_hr_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问人力资源配置功能，仅人力资源经理可以配置"
            )
        return current_user
    return hr_checker


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
        'admin',                # 管理员
        'super_admin',          # 超级管理员
        '系统管理员',
        '管理员',
        'gm',                   # 总经理
        '总经理',
        'chairman',             # 董事长
        '董事长',
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ''
        if role_code in admin_roles or role_name in admin_roles:
            return True

    return False


def require_scheduler_admin_access():
    """调度器管理权限检查依赖"""
    async def admin_checker(current_user: User = Depends(get_current_active_user)):
        if not has_scheduler_admin_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限管理调度器，仅管理员可以操作"
            )
        return current_user
    return admin_checker
