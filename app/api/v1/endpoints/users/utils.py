# -*- coding: utf-8 -*-
"""
用户管理 - 辅助工具函数
"""

from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.organization import Employee
from app.models.user import Role, User, UserRole
from app.schemas.auth import UserCreate, UserResponse


def get_role_names(user: User) -> List[str]:
    """提取用户角色名称"""
    roles = user.roles
    if hasattr(roles, "all"):
        roles = roles.all()
    return [ur.role.role_name for ur in roles] if roles else []


def get_role_ids(user: User) -> List[int]:
    """提取用户角色ID列表"""
    roles = user.roles
    if hasattr(roles, "all"):
        roles = roles.all()
    return [ur.role_id for ur in roles] if roles else []


def build_user_response(user: User) -> UserResponse:
    """构建用户响应"""
    return UserResponse(
        id=user.id,
        username=user.username,
        employee_id=getattr(user, "employee_id", None),
        email=user.email,
        phone=user.phone,
        real_name=user.real_name,
        employee_no=user.employee_no,
        department=user.department,
        position=user.position,
        avatar=user.avatar,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        last_login_at=user.last_login_at,
        roles=get_role_names(user),
        role_ids=get_role_ids(user),
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def generate_employee_code(db: Session) -> str:
    """生成新的员工编码"""
    from app.utils.number_generator import generate_employee_code
    return generate_employee_code(db)


def ensure_employee_unbound(db: Session, employee_id: int, current_user_id: Optional[int] = None) -> None:
    """确保员工尚未绑定其他账号"""
    existing = db.query(User).filter(User.employee_id == employee_id).first()
    if existing and existing.id != current_user_id:
        raise HTTPException(status_code=400, detail="该员工已绑定其他账号")


def prepare_employee_for_new_user(db: Session, user_in: UserCreate) -> Employee:
    """根据请求绑定或创建员工记录"""
    if user_in.employee_id:
        employee = db.query(Employee).filter(Employee.id == user_in.employee_id).first()
        if not employee:
            raise HTTPException(status_code=404, detail="员工不存在")
        ensure_employee_unbound(db, employee.id)
        return employee

    if user_in.employee_no:
        employee = (
            db.query(Employee)
                .filter(Employee.employee_code == user_in.employee_no)
                .first()
        )
        if employee:
            ensure_employee_unbound(db, employee.id)
            return employee

    employee = Employee(
        employee_code=user_in.employee_no or generate_employee_code(db),
        name=user_in.real_name or user_in.username,
        department=user_in.department,
        role=user_in.position,
        phone=user_in.phone,
    )
    db.add(employee)
    db.flush()
    return employee


def replace_user_roles(db: Session, user_id: int, role_ids: Optional[List[int]]) -> None:
    """替换用户角色"""
    if role_ids is None:
        return

    db.query(UserRole).filter(UserRole.user_id == user_id).delete()
    if not role_ids:
        return

    unique_ids = list(dict.fromkeys(role_ids))
    roles = db.query(Role).filter(Role.id.in_(unique_ids)).all()
    if len(roles) != len(unique_ids):
        raise HTTPException(status_code=400, detail="部分角色不存在")

    for role_id in unique_ids:
        db.add(UserRole(user_id=user_id, role_id=role_id))
