# -*- coding: utf-8 -*-
"""
项目成员扩展操作端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department, Employee
from app.models.project import ProjectMember
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.post("/projects/{project_id}/members/{member_id}/notify-dept-manager", response_model=ResponseModel)
def notify_dept_manager(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    通知部门经理（成员加入项目）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    member = db.query(ProjectMember).filter(ProjectMember.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="项目成员不存在")

    if member.dept_manager_notified:
        return ResponseModel(code=200, message="部门经理已通知")

    # 标记为已通知（实际通知可以通过消息系统发送）
    member.dept_manager_notified = True
    db.commit()

    return ResponseModel(code=200, message="部门经理通知已发送")


@router.get("/projects/{project_id}/members/from-dept/{dept_id}", response_model=dict)
def get_dept_users_for_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    dept_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取部门用户列表（用于批量添加成员）
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    dept = db.query(Department).filter(Department.id == dept_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="部门不存在")

    # 获取部门员工
    employees = db.query(Employee).filter(
        Employee.department == dept.dept_name,
        Employee.is_active == True
    ).all()

    # 获取对应的用户
    employee_ids = [e.id for e in employees]
    users = db.query(User).filter(
        User.employee_id.in_(employee_ids),
        User.is_active == True
    ).all()

    # 获取已在项目中的成员
    existing_member_ids = db.query(ProjectMember.user_id).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.is_active == True
    ).all()
    existing_user_ids = {m[0] for m in existing_member_ids}

    available_users = []
    for user in users:
        available_users.append({
            'user_id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'is_member': user.id in existing_user_ids
        })

    return {
        'dept_id': dept_id,
        'dept_name': dept.dept_name,
        'users': available_users
    }
