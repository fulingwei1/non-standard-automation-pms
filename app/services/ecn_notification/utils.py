# -*- coding: utf-8 -*-
"""
ECN通知服务 - 工具函数
包含：用户查找、部门查找等辅助函数
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.organization import Department
from app.models.user import User


def find_users_by_department(db: Session, department_name: str) -> List[User]:
    """
    根据部门名称查找用户

    Args:
        db: 数据库会话
        department_name: 部门名称

    Returns:
        List[User]: 用户列表
    """
    if not department_name:
        return []

    # 首先查找部门ID
    department = db.query(Department).filter(
        Department.name == department_name
    ).first()

    if not department:
        # 如果找不到部门，尝试通过用户表的department字段匹配
        users = db.query(User).filter(
            User.department == department_name,
            User.is_active
        ).all()
        return users

    # 通过部门ID查找用户
    users = db.query(User).filter(
        User.department_id == department.id,
        User.is_active
    ).all()

    return users


def find_users_by_role(db: Session, role_code: str) -> List[User]:
    """
    根据角色代码查找用户

    Args:
        db: 数据库会话
        role_code: 角色代码

    Returns:
        List[User]: 用户列表
    """
    if not role_code:
        return []

    users = db.query(User).join(
        User.roles
    ).filter(
        User.is_active
    ).all()

    # 过滤匹配的角色
    matched_users = []
    for user in users:
        for user_role in user.roles:
            if user_role.role:
                rc = user_role.role.role_code.lower() if user_role.role.role_code else ''
                rn = user_role.role.role_name.lower() if user_role.role.role_name else ''
                if rc == role_code.lower() or rn == role_code.lower():
                    matched_users.append(user)
                    break

    return matched_users


def find_department_manager(db: Session, department_id: Optional[int] = None) -> Optional[User]:
    """
    查找部门经理

    Args:
        db: 数据库会话
        department_id: 部门ID（可选）

    Returns:
        Optional[User]: 部门经理用户
    """
    if department_id:
        department = db.query(Department).filter(Department.id == department_id).first()
        if department and department.manager_id:
            return db.query(User).filter(User.id == department.manager_id).first()

    # 如果没有指定部门ID，尝试查找所有部门经理
    # 这里简化处理，实际可能需要更复杂的逻辑
    return None


def check_all_evaluations_completed(db: Session, ecn_id: int) -> bool:
    """
    检查ECN的所有评估是否都已完成

    Args:
        db: 数据库会话
        ecn_id: ECN ID

    Returns:
        bool: 是否所有评估都已完成
    """
    from app.models.ecn import EcnEvaluation

    evaluations = db.query(EcnEvaluation).filter(
        EcnEvaluation.ecn_id == ecn_id
    ).all()

    if not evaluations:
        return False

    return all(eval.status == 'COMPLETED' for eval in evaluations)
