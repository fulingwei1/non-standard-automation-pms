# -*- coding: utf-8 -*-
"""
销售提醒服务 - 基础工具函数
"""

from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.user import Role, User, UserRole


def find_users_by_role(db: Session, role_name: str) -> List[User]:
    """
    根据角色名称查找用户
    支持模糊匹配角色名称
    """
    if not role_name:
        return []

    # 查找匹配的角色
    roles = db.query(Role).filter(
        Role.is_active == True,
        or_(
            Role.role_name == role_name,
            Role.role_name.like(f"%{role_name}%"),
            Role.role_code.like(f"%{role_name}%")
        )
    ).all()

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
        User.is_active == True
    ).all()

    return users


def find_users_by_department(db: Session, dept_name: str) -> List[User]:
    """
    根据部门名称查找用户
    支持模糊匹配部门名称
    """
    if not dept_name:
        return []

    users = db.query(User).filter(
        User.is_active == True,
        or_(
            User.department == dept_name,
            User.department.like(f"%{dept_name}%")
        )
    ).all()
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
) -> Notification:
    """
    创建系统通知
    """
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        content=content,
        source_type=source_type,
        source_id=source_id,
        link_url=link_url,
        priority=priority,
        extra_data=extra_data or {}
    )
    db.add(notification)
    return notification
