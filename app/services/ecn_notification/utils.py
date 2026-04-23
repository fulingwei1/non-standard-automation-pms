# -*- coding: utf-8 -*-
"""ECN 通知旧工具函数兼容层。"""

from typing import List

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.user import Role, User, UserRole


def find_users_by_department(db: Session, department_name: str) -> List[User]:
    if not department_name:
        return []

    dept_name_field = getattr(Department, "name", None) or getattr(
        Department, "department_name", None
    )
    dept_query = db.query(Department)
    dept_query = (
        dept_query.filter(dept_name_field == department_name)
        if dept_name_field is not None
        else dept_query.filter(True)
    )
    dept = dept_query.first()
    if not dept:
        return []

    user_query = db.query(User).filter(User.department_id == dept.id)
    return user_query.filter(User.is_active).all()


def find_users_by_role(db: Session, role_code: str) -> List[User]:
    if not role_code:
        return []

    role_code_field = getattr(Role, "role_code", None) or getattr(Role, "code", None)
    role_query = db.query(Role)
    role_query = (
        role_query.filter(role_code_field == role_code)
        if role_code_field is not None
        else role_query.filter(True)
    )
    role = role_query.first()
    if not role:
        return []

    user_roles = db.query(UserRole).filter(UserRole.role_id == role.id).all()
    user_ids = list({ur.user_id for ur in user_roles if getattr(ur, "user_id", None)})
    if not user_ids:
        return []

    return db.query(User).filter(User.id.in_(user_ids)).filter(User.is_active).all()
