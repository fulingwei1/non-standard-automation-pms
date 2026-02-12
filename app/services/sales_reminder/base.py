# -*- coding: utf-8 -*-
"""
销售提醒服务 - 基础工具函数
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.user import Role, User, UserRole
from app.services.notification_dispatcher import NotificationDispatcher


def find_users_by_role(db: Session, role_name: str) -> List[User]:
    """
    根据角色名称查找用户
    支持模糊匹配角色名称
    """
    if not role_name:
        return []

    # 查找匹配的角色
    roles_query = db.query(Role).filter(Role.is_active)
    roles_query = apply_keyword_filter(
        roles_query,
        Role,
        role_name,
        ["role_name", "role_code"],
        use_ilike=False,
    )
    roles = roles_query.all()

    if not roles:
        return []

    role_ids = [r.id for r in roles]

    # 查找拥有这些角色的用户
    user_roles = db.query(UserRole).filter(
        UserRole.role_id.in_(role_ids)
    ).all()

    user_ids = list(set([ur.user_id for ur in user_roles]))

    if not user_ids:
        return []

    users = db.query(User).filter(
        User.id.in_(user_ids),
        User.is_active
    ).all()

    return users


def find_users_by_department(db: Session, dept_name: str) -> List[User]:
    """
    根据部门名称查找用户
    支持模糊匹配部门名称
    """
    if not dept_name:
        return []

    users_query = db.query(User).filter(User.is_active)
    users_query = apply_keyword_filter(
        users_query,
        User,
        dept_name,
        "department",
        use_ilike=False,
    )
    users = users_query.all()
    return users


def create_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    content: str,
    source_type: Optional[str] = None,
    source_id: Optional[int] = None,
    link_url: Optional[str] = None,
    priority: str = "NORMAL",
    extra_data: Optional[dict] = None
) -> object:
    """
    创建系统通知
    """
    dispatcher = NotificationDispatcher(db)
    return dispatcher.create_system_notification(
        recipient_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        link_url=link_url,
        priority=priority,
        extra_data=extra_data or {},
    )
