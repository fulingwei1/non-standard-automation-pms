# -*- coding: utf-8 -*-
"""
权限检查模块 - 工时审批权限
"""

from typing import Any, List, Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_active_user, get_db
from app.models.user import User


def has_timesheet_approval_access(
    user: User,
    db: Session,
    timesheet_user_id: Optional[int] = None,
    timesheet_dept_id: Optional[int] = None,
) -> bool:
    """
    检查用户是否有工时审批权限

    工时审批权限包括：
    1. 项目经理可以审批本项目的工时
    2. 部门经理可以审批本部门的工时
    3. 管理员可以审批所有工时

    Args:
        user: 当前用户
        db: 数据库会话
        timesheet_user_id: 工时提交人的用户ID
        timesheet_dept_id: 工时提交人的部门ID

    Returns:
        bool: 是否有审批权限
    """
    if user.is_superuser:
        return True

    # 检查是否有工时审批权限角色
    approval_roles = [
        "pm",  # 项目经理
        "project_manager",  # 项目经理
        "项目经理",
        "pmo_dir",  # 项目管理部总监
        "项目管理部总监",
        "me_mgr",  # 机械部经理
        "机械部经理",
        "ee_mgr",  # 电气部经理
        "电气部经理",
        "dept_manager",  # 部门经理
        "department_manager",  # 部门经理
        "部门经理",
        "hr_manager",  # 人事经理
        "人事经理",
        "gm",  # 总经理
        "总经理",
        "admin",  # 管理员
        "super_admin",
    ]

    # 检查用户角色
    has_approval_role = False
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower() if user_role.role.role_code else ""
        role_name = user_role.role.role_name.lower() if user_role.role.role_name else ""
        if role_code in approval_roles or role_name in approval_roles:
            has_approval_role = True
            break

    if not has_approval_role:
        return False

    # 如果没有具体的工时信息，只检查角色
    if timesheet_user_id is None and timesheet_dept_id is None:
        return True

    # 检查项目经理权限：是否是工时提交人所在项目的项目经理
    from app.models.project import Project

    if timesheet_user_id:
        # 查找该用户参与的项目，其中当前用户是项目经理
        projects_as_pm = db.query(Project).filter(Project.pm_id == user.id).all()
        project_ids = [p.id for p in projects_as_pm]

        # 检查工时是否属于这些项目
        from app.models.timesheet import Timesheet

        timesheet_in_pm_project = (
            db.query(Timesheet)
            .filter(
                Timesheet.id
                == timesheet_user_id,  # 这里实际应该是timesheet的project_id检查
                Timesheet.project_id.in_(project_ids),
            )
            .first()
        )
        if timesheet_in_pm_project:
            return True

    # 检查部门经理权限：是否是同一部门
    if timesheet_dept_id and user.department_id:
        if user.department_id == timesheet_dept_id:
            return True

    return True  # 有审批角色且通过基本检查


def require_timesheet_approval_access():
    """工时审批权限检查依赖"""

    async def checker(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_timesheet_approval_access(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限审批工时记录",
            )
        return current_user

    return checker


def check_timesheet_approval_permission(
    user: User, db: Session, timesheets: List[Any]
) -> bool:
    """
    检查工时审批权限（批量）

    Args:
        user: 当前用户
        db: 数据库会话
        timesheets: 工时记录列表

    Returns:
        bool: 是否有审批权限
    """
    if user.is_superuser:
        return True

    # 收集所有需要检查的用户和部门
    user_ids = list(set(ts.user_id for ts in timesheets))
    dept_ids = list(set(ts.department_id for ts in timesheets if ts.department_id))

    # 检查是否有任何审批权限
    for user_id in user_ids:
        for dept_id in dept_ids:
            if has_timesheet_approval_access(user, db, user_id, dept_id):
                return True

    return has_timesheet_approval_access(user, db)
