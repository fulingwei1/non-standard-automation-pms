# -*- coding: utf-8 -*-
"""
销售权限模块 - 销售数据范围过滤、创建/编辑/删除权限
"""

import logging
from typing import Any, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..models.user import User
from .auth import get_current_active_user, get_db, is_superuser

logger = logging.getLogger(__name__)

__all__ = [
    "get_sales_data_scope",
    "filter_sales_data_by_scope",
    "filter_sales_finance_data_by_scope",
    "check_sales_create_permission",
    "check_sales_edit_permission",
    "check_sales_delete_permission",
    "require_sales_create_permission",
    "require_sales_edit_permission",
    "require_sales_delete_permission",
    "has_sales_assessment_access",
    "require_sales_assessment_access",
    "has_sales_approval_access",
    "check_sales_approval_permission",
    "require_sales_approval_permission",
    "can_manage_sales_opportunity",
    "can_set_opportunity_gate",
]


def get_sales_data_scope(user: User, db: Session) -> str:
    """
    获取销售数据权限范围（基于数据库角色配置）

    完全基于数据库中角色的 data_scope 字段，不再硬编码角色代码。
    管理员可以在角色管理中配置每个角色的数据权限范围。

    Returns:
        'ALL': 可以看到所有数据
        'DEPT': 可以看到部门数据
        'TEAM': 可以看到团队数据（下属）
        'PROJECT': 可以看到参与项目的数据
        'OWN': 只能看到自己的数据
        'FINANCE_ONLY': 财务专用 - 只能看到发票和收款数据
        'NONE': 无权限
    """
    from app.core.auth import is_superuser
    
    if is_superuser(user):
        return "ALL"

    # 使用 DataScopeService 获取用户的数据权限范围
    from app.services.data_scope import DataScopeService

    db_scope = DataScopeService.get_user_data_scope(db, user)

    # 映射数据库的 DataScopeEnum 值到销售模块使用的值
    # 数据库值: ALL, DEPT, SUBORDINATE, PROJECT, OWN, CUSTOMER
    scope_mapping = {
        "ALL": "ALL",
        "DEPT": "DEPT",
        "SUBORDINATE": "TEAM",  # 下属 -> 团队
        "PROJECT": "PROJECT",
        "OWN": "OWN",
        "CUSTOMER": "OWN",  # 客户门户降级为个人
    }

    sales_scope = scope_mapping.get(db_scope, "OWN")

    # 特殊处理：检查是否是财务角色（财务对于发票/收款有特殊权限）
    # 这里通过检查角色是否有 FINANCE 相关权限来判断
    for user_role in user.roles:
        if user_role.role and user_role.role.is_active:
            role_code = (user_role.role.role_code or "").upper()
            # 财务角色：如果数据范围是 ALL，则保持 ALL；否则标记为 FINANCE_ONLY
            if role_code in ["FINANCE", "FI", "CFO", "财务", "财务人员", "财务专员", "财务经理", "财务总监"]:
                if sales_scope != "ALL":
                    return "FINANCE_ONLY"

    return sales_scope


def filter_sales_data_by_scope(
    query,
    user: User,
    db: Session,
    model_class,
    owner_field_name: str = "owner_id",
) -> Any:
    """
    根据销售数据权限范围过滤查询（基于数据库配置）

    Args:
        query: SQLAlchemy 查询对象
        user: 当前用户
        db: 数据库会话
        model_class: 模型类（用于获取字段）
        owner_field_name: 负责人字段名（默认 'owner_id'）

    Returns:
        过滤后的查询对象
    """

    from app.models.organization import Department
    from app.services.data_scope import DataScopeService

    scope = get_sales_data_scope(user, db)
    owner_field = getattr(model_class, owner_field_name, None)

    if scope == "ALL":
        # 全部可见：不进行任何过滤
        return query

    elif scope == "DEPT":
        # 部门可见：同部门用户的数据
        if user.department and owner_field is not None:
            dept = (
                db.query(Department)
                .filter(Department.dept_name == user.department)
                .first()
            )
            if dept:
                from ..models.user import User as UserModel
                dept_users = (
                    db.query(UserModel).filter(UserModel.department == user.department).all()
                )
                dept_user_ids = [u.id for u in dept_users]
                return query.filter(owner_field.in_(dept_user_ids + [user.id]))
        # 无部门信息，降级为 OWN
        if owner_field is not None:
            return query.filter(owner_field == user.id)
        return query.filter(False)

    elif scope == "TEAM":
        # 团队可见：自己 + 直接下属的数据
        if owner_field is not None:
            subordinate_ids = DataScopeService.get_subordinate_ids(db, user.id)
            allowed_user_ids = list(subordinate_ids | {user.id})
            return query.filter(owner_field.in_(allowed_user_ids))
        return query.filter(False)

    elif scope == "PROJECT":
        # 项目可见：参与项目相关的数据
        # 对于销售数据，降级为 OWN（销售数据通常不按项目划分）
        if owner_field is not None:
            return query.filter(owner_field == user.id)
        return query.filter(False)

    elif scope == "OWN":
        # 个人可见：只能看到自己的数据
        if owner_field is not None:
            return query.filter(owner_field == user.id)
        return query.filter(False)

    elif scope == "FINANCE_ONLY":
        # 财务专用：对于非发票/收款数据，返回空结果
        # 发票和收款使用 filter_sales_finance_data_by_scope
        return query.filter(False)

    else:
        # 无权限：返回空结果
        return query.filter(False)


def filter_sales_finance_data_by_scope(
    query,
    user: User,
    db: Session,
    model_class,
    owner_field_name: str = "owner_id",
) -> Any:
    """
    财务数据权限过滤（发票和收款）

    财务角色可以看到所有发票和收款数据，其他角色按数据权限范围过滤。
    """
    from app.models.organization import Department
    from app.services.data_scope import DataScopeService

    scope = get_sales_data_scope(user, db)
    owner_field = getattr(model_class, owner_field_name, None)

    if scope in ["ALL", "FINANCE_ONLY"]:
        # 全部可见 或 财务专用：可以看到所有发票和收款数据
        return query

    # 其他角色按数据权限范围过滤
    if scope == "DEPT":
        # 部门可见：同部门用户的数据
        if user.department and owner_field is not None:
            dept = (
                db.query(Department)
                .filter(Department.dept_name == user.department)
                .first()
            )
            if dept:
                from ..models.user import User as UserModel
                dept_users = (
                    db.query(UserModel).filter(UserModel.department == user.department).all()
                )
                dept_user_ids = [u.id for u in dept_users]
                return query.filter(owner_field.in_(dept_user_ids + [user.id]))
        # 无部门信息，降级为 OWN
        if owner_field is not None:
            return query.filter(owner_field == user.id)
        return query.filter(False)

    elif scope == "TEAM":
        # 团队可见：自己 + 直接下属的数据
        if owner_field is not None:
            subordinate_ids = DataScopeService.get_subordinate_ids(db, user.id)
            allowed_user_ids = list(subordinate_ids | {user.id})
            return query.filter(owner_field.in_(allowed_user_ids))
        return query.filter(False)

    elif scope == "PROJECT":
        # 项目可见：参与项目相关的数据
        # 对于财务数据，降级为 OWN
        if owner_field is not None:
            return query.filter(owner_field == user.id)
        return query.filter(False)

    elif scope == "OWN":
        # 个人可见：只能看到自己的数据
        if owner_field is not None:
            return query.filter(owner_field == user.id)
        return query.filter(False)

    else:
        # 无权限：返回空结果
        return query.filter(False)


def can_manage_sales_opportunity(db: Session, user: User, opportunity) -> bool:
    """
    判断用户是否可以管理指定商机（自身/团队/部门/全部）。
    """
    if is_superuser(user):
        return True

    if getattr(opportunity, "owner_id", None) == user.id:
        return True

    scope = get_sales_data_scope(user, db)
    if scope == "ALL":
        return True

    owner_id = getattr(opportunity, "owner_id", None)
    if not owner_id:
        return False

    if scope == "DEPT":
        if not user.department:
            return False
        owner = db.query(User).filter(User.id == owner_id).first()
        return owner is not None and owner.department == user.department

    if scope == "TEAM":
        from app.services.data_scope.user_scope import UserScopeService

        subordinate_ids = UserScopeService.get_subordinate_ids(db, user.id)
        return owner_id in subordinate_ids

    return False


def can_set_opportunity_gate(db: Session, user: User, opportunity) -> bool:
    """
    判断用户是否可以设置商机阶段门（经理/总监级别）。
    """
    if is_superuser(user):
        return True

    scope = get_sales_data_scope(user, db)
    if scope in {"ALL", "DEPT", "TEAM"}:
        return can_manage_sales_opportunity(db, user, opportunity)

    # 其他权限范围不能设置商机阶段门
    return False


def check_sales_create_permission(user: User, db: Session) -> bool:
    """
    检查销售数据创建权限

    创建权限：有数据范围权限的用户都可以创建
    """
    if is_superuser(user):
        return True

    scope = get_sales_data_scope(user, db)
    # 除了 FINANCE_ONLY 和 NONE，其他都可以创建
    return scope in ["ALL", "DEPT", "TEAM", "PROJECT", "OWN"]


def check_sales_edit_permission(
    user: User,
    db: Session,
    entity_created_by: Optional[int] = None,
    entity_owner_id: Optional[int] = None,
) -> bool:
    """
    检查销售数据编辑权限

    编辑权限规则：
    - ALL/DEPT/TEAM: 可以编辑权限范围内的所有数据
    - PROJECT/OWN: 只能编辑自己创建或负责的数据
    """
    if is_superuser(user):
        return True

    scope = get_sales_data_scope(user, db)

    # ALL、DEPT、TEAM 可以编辑范围内的数据
    if scope in ["ALL", "DEPT", "TEAM"]:
        return True

    # PROJECT、OWN 只能编辑自己创建或负责的数据
    if scope in ["PROJECT", "OWN"]:
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
    检查销售数据删除权限

    删除权限规则：
    - ALL: 可以删除所有数据
    - 其他: 只有创建人可以删除自己的数据
    """
    if is_superuser(user):
        return True

    scope = get_sales_data_scope(user, db)

    # ALL 可以删除所有数据
    if scope == "ALL":
        return True

    # 只有创建人可以删除自己的数据
    if entity_created_by and entity_created_by == user.id:
        return True

    return False


def require_sales_create_permission():
    """Issue 7.2: 销售数据创建权限检查依赖"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not check_sales_create_permission(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限创建销售数据"
            )
        return current_user

    return permission_checker


def require_sales_edit_permission(
    entity_created_by: Optional[int] = None, entity_owner_id: Optional[int] = None
):
    """Issue 7.2: 销售数据编辑权限检查依赖"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not check_sales_edit_permission(
            current_user, db, entity_created_by, entity_owner_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限编辑此数据"
            )
        return current_user

    return permission_checker


def require_sales_delete_permission(entity_created_by: Optional[int] = None):
    """Issue 7.2: 销售数据删除权限检查依赖"""

    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not check_sales_delete_permission(current_user, db, entity_created_by):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限删除此数据"
            )
        return current_user

    return permission_checker


def has_sales_assessment_access(user: User, db: Session = None) -> bool:
    """
    检查用户是否有技术评估权限

    基于数据权限范围判断：
    - ALL, DEPT, TEAM, PROJECT, OWN 都有评估权限
    - FINANCE_ONLY 没有评估权限（财务不参与技术评估）
    """
    if is_superuser(user):
        return True

    # 如果提供了 db，使用数据权限范围判断
    if db:
        scope = get_sales_data_scope(user, db)
        # 除了财务和无权限，其他都可以做技术评估
        return scope in ["ALL", "DEPT", "TEAM", "PROJECT", "OWN"]

    # 兼容旧代码：没有 db 时，检查用户是否有任何活跃角色
    for user_role in user.roles:
        if user_role.role and user_role.role.is_active:
            return True

    return False


def require_sales_assessment_access():
    """技术评估权限检查依赖"""

    async def assessment_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not has_sales_assessment_access(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限进行技术评估"
            )
        return current_user

    return assessment_checker


def has_sales_approval_access(user: User, db: Session) -> bool:
    """
    检查用户是否有销售审批权限（报价审批、合同审批、发票审批）

    基于数据权限范围判断：
    - ALL: 高级管理层，有全部审批权限
    - DEPT: 部门经理，有部门级审批权限
    - TEAM: 团队负责人，有团队级审批权限
    - 其他: 没有审批权限
    """
    if is_superuser(user):
        return True

    scope = get_sales_data_scope(user, db)
    # 只有 ALL、DEPT、TEAM 级别的用户有审批权限
    return scope in ["ALL", "DEPT", "TEAM"]


def check_sales_approval_permission(user: User, approval: Any, db: Session) -> bool:
    """
    检查销售审批权限（基于数据权限范围）

    Args:
        user: 当前用户
        approval: 审批对象（QuoteApproval/ContractApproval/InvoiceApproval）
        db: 数据库会话

    Returns:
        bool: 是否有审批权限

    审批级别与数据权限范围映射：
    - 一级审批(level=1): DEPT, TEAM 级别用户可以审批
    - 二级及以上审批(level>=2): 只有 ALL 级别用户可以审批
    """
    if is_superuser(user):
        return True

    # 检查用户是否有基本审批权限
    if not has_sales_approval_access(user, db):
        return False

    # 检查审批级别是否匹配用户角色
    approval_level = getattr(approval, "approval_level", 1)
    approval_role = getattr(approval, "approval_role", "")

    # 如果指定了审批角色，检查用户是否具有该角色
    if approval_role:
        for user_role in user.roles:
            if user_role.role and user_role.role.role_code == approval_role:
                return True

    # 根据数据权限范围和审批级别判断
    scope = get_sales_data_scope(user, db)

    if approval_level == 1:
        # 一级审批：DEPT, TEAM, ALL 都可以
        return scope in ["ALL", "DEPT", "TEAM"]
    elif approval_level >= 2:
        # 二级及以上审批：只有 ALL 级别可以
        return scope == "ALL"

    return False


def require_sales_approval_permission():
    """销售审批权限检查依赖"""

    async def approval_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ):
        if not has_sales_approval_access(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="您没有权限进行审批操作"
            )
        return current_user

    return approval_checker
