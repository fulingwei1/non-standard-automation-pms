# -*- coding: utf-8 -*-
"""
销售权限模块

包含销售数据权限范围、销售数据CRUD权限、销售评估和审批权限
"""

from typing import Optional, Any, List

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...models.user import User
from .deps import get_db, get_current_active_user


def get_sales_data_scope(user: User, db: Session) -> str:
    """
    Issue 7.1: 获取销售数据权限范围

    Returns:
        'ALL': 销售总监 - 可以看到所有数据
        'TEAM': 销售经理 - 可以看到团队数据（同部门或下属）
        'OWN': 销售 - 只能看到自己的数据
        'FINANCE_ONLY': 财务 - 只能看到发票和收款数据
        'NONE': 无权限
    """
    if user.is_superuser:
        return 'ALL'

    # 获取用户所有角色的角色代码
    role_codes = set()
    for user_role in user.roles:
        if user_role.role and user_role.role.is_active:
            role_code = (user_role.role.role_code or '').upper()
            role_codes.add(role_code)

    # 优先级：SALES_DIRECTOR > SALES_MANAGER > FINANCE > SALES
    if any(code in ['SALES_DIRECTOR', 'SALESDIRECTOR', '销售总监'] for code in role_codes):
        return 'ALL'
    elif any(code in ['SALES_MANAGER', 'SALESMANAGER', '销售经理'] for code in role_codes):
        return 'TEAM'
    elif any(code in ['FINANCE', '财务', 'FINANCE_MANAGER', '财务经理'] for code in role_codes):
        return 'FINANCE_ONLY'
    elif any(code in ['SALES', '销售', 'PRESALES', '售前'] for code in role_codes):
        return 'OWN'

    return 'NONE'


def filter_sales_data_by_scope(
    query,
    user: User,
    db: Session,
    model_class,
    owner_field_name: str = 'owner_id',
) -> Any:
    """
    Issue 7.1: 根据销售数据权限范围过滤查询

    Args:
        query: SQLAlchemy 查询对象
        user: 当前用户
        db: 数据库会话
        model_class: 模型类（用于获取字段）
        owner_field_name: 负责人字段名（默认 'owner_id'）

    Returns:
        过滤后的查询对象
    """
    scope = get_sales_data_scope(user, db)

    if scope == 'ALL':
        # 销售总监：不进行任何过滤
        return query
    elif scope == 'TEAM':
        # 销售经理：可以看到团队数据（同部门或下属）
        from ...models.organization import Department

        # 获取用户部门
        if user.department:
            dept = db.query(Department).filter(Department.dept_name == user.department).first()
            if dept:
                # 同部门的所有用户ID
                dept_users = db.query(User).filter(User.department == user.department).all()
                dept_user_ids = [u.id for u in dept_users]
                # 过滤：负责人是同部门的用户，或者是当前用户
                owner_field = getattr(model_class, owner_field_name)
                return query.filter(owner_field.in_(dept_user_ids + [user.id]))

        # 如果没有部门信息，降级为OWN
        owner_field = getattr(model_class, owner_field_name)
        return query.filter(owner_field == user.id)
    elif scope == 'OWN':
        # 销售：只能看到自己的数据
        owner_field = getattr(model_class, owner_field_name)
        return query.filter(owner_field == user.id)
    elif scope == 'FINANCE_ONLY':
        # 财务：对于非发票/收款数据，返回空结果
        # 这个函数主要用于线索/商机/报价/合同，发票和收款有单独的过滤逻辑
        return query.filter(False)  # 返回空结果
    else:
        # 无权限：返回空结果
        return query.filter(False)


def filter_sales_finance_data_by_scope(
    query,
    user: User,
    db: Session,
    model_class,
    owner_field_name: str = 'owner_id',
) -> Any:
    """
    Issue 7.1: 财务数据权限过滤（发票和收款）
    财务可以看到所有发票和收款数据
    """
    scope = get_sales_data_scope(user, db)

    if scope in ['ALL', 'FINANCE_ONLY']:
        # 销售总监和财务：可以看到所有发票和收款数据
        return query
    elif scope == 'TEAM':
        # 销售经理：可以看到团队数据
        from ...models.organization import Department

        if user.department:
            dept = db.query(Department).filter(Department.dept_name == user.department).first()
            if dept:
                dept_users = db.query(User).filter(User.department == user.department).all()
                dept_user_ids = [u.id for u in dept_users]
                owner_field = getattr(model_class, owner_field_name)
                return query.filter(owner_field.in_(dept_user_ids + [user.id]))

        owner_field = getattr(model_class, owner_field_name)
        return query.filter(owner_field == user.id)
    elif scope == 'OWN':
        # 销售：只能看到自己的数据
        owner_field = getattr(model_class, owner_field_name)
        return query.filter(owner_field == user.id)
    else:
        return query.filter(False)


def check_sales_create_permission(user: User, db: Session) -> bool:
    """
    Issue 7.2: 检查销售数据创建权限
    创建权限：销售、销售经理、销售总监
    """
    if user.is_superuser:
        return True

    scope = get_sales_data_scope(user, db)
    return scope in ['ALL', 'TEAM', 'OWN']


def check_sales_edit_permission(
    user: User,
    db: Session,
    entity_created_by: Optional[int] = None,
    entity_owner_id: Optional[int] = None,
) -> bool:
    """
    Issue 7.2: 检查销售数据编辑权限
    编辑权限：创建人、负责人、销售经理、销售总监
    """
    if user.is_superuser:
        return True

    scope = get_sales_data_scope(user, db)

    # 销售总监和销售经理可以编辑所有数据
    if scope in ['ALL', 'TEAM']:
        return True

    # 销售只能编辑自己创建或负责的数据
    if scope == 'OWN':
        if entity_created_by and entity_created_by == user.id:
            return True
        if entity_owner_id and entity_owner_id == user.id:
            return True
        return False

    return False


def check_sales_delete_permission(
    user: User,
    db: Session,
    entity_created_by: Optional[int] = None,
) -> bool:
    """
    Issue 7.2: 检查销售数据删除权限
    删除权限：仅创建人、销售总监、管理员
    """
    if user.is_superuser:
        return True

    scope = get_sales_data_scope(user, db)

    # 销售总监可以删除所有数据
    if scope == 'ALL':
        return True

    # 只有创建人可以删除自己的数据
    if entity_created_by and entity_created_by == user.id:
        return True

    return False


def require_sales_create_permission():
    """Issue 7.2: 销售数据创建权限检查依赖"""
    async def permission_checker(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        if not check_sales_create_permission(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限创建销售数据"
            )
        return current_user
    return permission_checker


def require_sales_edit_permission(entity_created_by: Optional[int] = None, entity_owner_id: Optional[int] = None):
    """Issue 7.2: 销售数据编辑权限检查依赖"""
    async def permission_checker(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        if not check_sales_edit_permission(current_user, db, entity_created_by, entity_owner_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限编辑此数据"
            )
        return current_user
    return permission_checker


def require_sales_delete_permission(entity_created_by: Optional[int] = None):
    """Issue 7.2: 销售数据删除权限检查依赖"""
    async def permission_checker(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        if not check_sales_delete_permission(current_user, db, entity_created_by):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限删除此数据"
            )
        return current_user
    return permission_checker


def has_sales_assessment_access(user: User) -> bool:
    """检查用户是否有技术评估权限"""
    if user.is_superuser:
        return True

    # 定义有技术评估权限的角色代码
    assessment_roles = [
        'sales',
        'sales_engineer',
        'sales_manager',
        'sales_director',
        'presales_engineer',
        'presales_manager',
        'te',  # 技术工程师
        'technical_engineer',
        'admin',
        'super_admin',
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in assessment_roles:
            return True

    return False


def require_sales_assessment_access():
    """技术评估权限检查依赖"""
    async def assessment_checker(current_user: User = Depends(get_current_active_user)):
        if not has_sales_assessment_access(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行技术评估"
            )
        return current_user
    return assessment_checker


def has_sales_approval_access(user: User, db: Session) -> bool:
    """
    检查用户是否有销售审批权限
    包括：报价审批、合同审批、发票审批
    """
    if user.is_superuser:
        return True

    # 定义有审批权限的角色代码
    approval_roles = [
        'sales_manager',         # 销售经理
        '销售经理',
        'sales_director',        # 销售总监
        '销售总监',
        'finance_manager',       # 财务经理
        '财务经理',
        'finance_director',      # 财务总监
        '财务总监',
        'gm',                    # 总经理
        '总经理',
        'chairman',              # 董事长
        '董事长',
        'admin',                 # 系统管理员
        'super_admin',           # 超级管理员
    ]

    # 检查用户角色
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ''
        if role_code in approval_roles:
            return True

    return False


def check_sales_approval_permission(user: User, approval: Any, db: Session) -> bool:
    """
    检查销售审批权限

    Args:
        user: 当前用户
        approval: 审批对象（QuoteApproval/ContractApproval/InvoiceApproval）
        db: 数据库会话

    Returns:
        bool: 是否有审批权限
    """
    if user.is_superuser:
        return True

    # 检查用户是否有审批权限角色
    if not has_sales_approval_access(user, db):
        return False

    # 检查审批级别是否匹配用户角色
    approval_level = getattr(approval, 'approval_level', 1)
    approval_role = getattr(approval, 'approval_role', '')

    # 如果指定了审批角色，检查用户是否具有该角色
    if approval_role:
        for user_role in user.roles:
            if user_role.role.role_code == approval_role:
                return True

    # 根据审批级别检查权限
    if approval_level == 1:
        # 一级审批：销售经理、财务经理
        level1_roles = ['sales_manager', '销售经理', 'finance_manager', '财务经理']
        for user_role in user.roles:
            if user_role.role.role_code.lower() in level1_roles:
                return True

    elif approval_level >= 2:
        # 二级及以上审批：销售总监、财务总监、总经理
        level2_roles = ['sales_director', '销售总监', 'finance_director', '财务总监',
                       'gm', '总经理', 'chairman', '董事长']
        for user_role in user.roles:
            if user_role.role.role_code.lower() in level2_roles:
                return True

    return False


def require_sales_approval_permission():
    """销售审批权限检查依赖"""
    async def approval_checker(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
        if not has_sales_approval_access(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限进行审批操作"
            )
        return current_user
    return approval_checker
