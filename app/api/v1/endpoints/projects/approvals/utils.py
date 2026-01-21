# -*- coding: utf-8 -*-
"""
项目审批工具函数

提供审批相关的辅助函数
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.sales.workflow import ApprovalWorkflowStep
from app.models.user import Role, User, UserRole

logger = logging.getLogger(__name__)

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"


def get_user_display_name(db: Session, user_id: Optional[int]) -> Optional[str]:
    """获取用户显示名称"""
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.display_name if user else None


def _check_approval_permission(
    db: Session,
    current_user: User,
    step: ApprovalWorkflowStep
) -> bool:
    """
    检查当前用户是否有权限审批该步骤

    Args:
        db: 数据库会话
        current_user: 当前用户
        step: 审批步骤

    Returns:
        是否有权限审批
    """
    # 超级管理员始终有权限
    if current_user.is_superuser:
        return True

    # 1. 检查是否是指定审批人
    if step.approver_id:
        if current_user.id == step.approver_id:
            return True

    # 2. 检查是否具有审批角色
    if step.approver_role:
        # 查询用户是否具有该角色
        user_has_role = (
            db.query(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .filter(
                UserRole.user_id == current_user.id,
                Role.role_code == step.approver_role,
                Role.is_active == True,
            )
            .first()
        )

        if user_has_role:
            return True

    # 3. 如果步骤既没有指定审批人也没有指定角色，则所有人都可以审批（向后兼容）
    if not step.approver_id and not step.approver_role:
        logger.warning(f"审批步骤 {step.step_name} 未配置审批人或角色，允许任何用户审批")
        return True

    return False



def get_user_display_name(db: Session, user_id: Optional[int]) -> Optional[str]:
    """获取用户显示名称"""
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.display_name if user else None


def _check_approval_permission(
    db: Session,
    current_user: User,
    step: ApprovalWorkflowStep
) -> bool:
    """
    检查当前用户是否有权限审批该步骤

    Args:
        db: 数据库会话
        current_user: 当前用户
        step: 审批步骤

    Returns:
        是否有权限审批
    """
    # 超级管理员始终有权限
    if current_user.is_superuser:
        return True

    # 1. 检查是否是指定审批人
    if step.approver_id:
        if current_user.id == step.approver_id:
            return True

    # 2. 检查是否具有审批角色
    if step.approver_role:
        from app.models.user import Role, UserRole

        # 查询用户是否具有该角色
        user_has_role = (
            db.query(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .filter(
                UserRole.user_id == current_user.id,
                Role.role_code == step.approver_role,
                Role.is_active == True,
            )
            .first()
        )

        if user_has_role:
            return True

    # 3. 如果步骤既没有指定审批人也没有指定角色，则所有人都可以审批（向后兼容）
    if not step.approver_id and not step.approver_role:
        logger.warning(f"审批步骤 {step.step_name} 未配置审批人或角色，允许任何用户审批")
        return True

    return False

