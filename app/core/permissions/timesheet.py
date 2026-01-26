# -*- coding: utf-8 -*-
"""
权限检查模块 - 工时审批权限
"""

from typing import List, Optional, Set, Dict, Any
from sqlalchemy.orm import Session, Query
from fastapi import Depends, HTTPException, status

from app.core.auth import get_current_active_user
from app.models.organization import Department
from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.timesheet import Timesheet
from app.models.user import User


def is_timesheet_admin(user: User) -> bool:
    """
    检查用户是否具有工时管理/审批的全局权限（超级管理员或特定管理角色）
    """
    if hasattr(user, "is_superuser") and user.is_superuser:
        return True

    # 检查是否具有相关管理角色
    admin_role_codes = {
        "admin",
        "super_admin",
        "system_admin",
        "hr_admin",
        "timesheet_admin",
    }
    admin_role_names = {
        "系统管理员",
        "超级管理员",
        "管理员",
        "人事管理员",
        "工时管理员",
    }

    roles = getattr(user, "roles", None)
    if not roles:
        return False

    if hasattr(roles, "all"):
        roles = roles.all()

    for user_role in roles:
        role = getattr(user_role, "role", user_role)
        role_code = (getattr(role, "role_code", "") or "").lower()
        role_name = getattr(role, "role_name", "") or ""
        if role_code in admin_role_codes or role_name in admin_role_names:
            return True

    return False


def get_user_manageable_dimensions(db: Session, user: User) -> Dict[str, Any]:
    """
    获取用户可管理的维度 IDs
    返回: {
        "is_admin": bool,
        "project_ids": Set[int],
        "rd_project_ids": Set[int],
        "department_ids": Set[int],
        "subordinate_user_ids": Set[int]
    }
    """
    result = {
        "is_admin": is_timesheet_admin(user),
        "project_ids": set(),
        "rd_project_ids": set(),
        "department_ids": set(),
        "subordinate_user_ids": set(),
    }

    if result["is_admin"]:
        return result

    # 1. 查找管理的非标项目
    managed_projects = db.query(Project.id).filter(Project.pm_id == user.id).all()
    result["project_ids"] = {p.id for p in managed_projects}

    # 2. 查找管理的研发项目
    managed_rd_projects = (
        db.query(RdProject.id).filter(RdProject.project_manager_id == user.id).all()
    )
    result["rd_project_ids"] = {p.id for p in managed_rd_projects}

    # 3. 查找管理的部门 (manager_id 可能是 employee_id)
    dept_query = db.query(Department.id)
    if hasattr(user, "employee_id") and user.employee_id:
        dept_query = dept_query.filter(
            (Department.manager_id == user.id)
            | (Department.manager_id == user.employee_id)
        )
    else:
        dept_query = dept_query.filter(Department.manager_id == user.id)

    managed_depts = dept_query.all()
    result["department_ids"] = {d.id for d in managed_depts}

    # 4. 查找直接下属人 (reporting_to)
    subordinates = db.query(User.id).filter(User.reporting_to == user.id).all()
    result["subordinate_user_ids"] = {s.id for s in subordinates}

    return result


def apply_timesheet_access_filter(
    query: Query, db: Session, current_user: User
) -> Query:
    """
    统一工时数据访问权限过滤
    """
    if is_timesheet_admin(current_user):
        return query

    dims = get_user_manageable_dimensions(db, current_user)

    # 过滤条件集合
    filters = []

    # 1. 自己的工时
    filters.append(Timesheet.user_id == current_user.id)

    # 2. 我管理的项目的工时
    if dims["project_ids"]:
        filters.append(Timesheet.project_id.in_(list(dims["project_ids"])))

    # 3. 我管理的研发项目的工时
    if dims["rd_project_ids"]:
        filters.append(Timesheet.rd_project_id.in_(list(dims["rd_project_ids"])))

    # 4. 我管理的部门的工时
    if dims["department_ids"]:
        filters.append(Timesheet.department_id.in_(list(dims["department_ids"])))

    # 5. 我下属的工时
    if dims["subordinate_user_ids"]:
        filters.append(Timesheet.user_id.in_(list(dims["subordinate_user_ids"])))

    from sqlalchemy import or_

    return query.filter(or_(*filters))


def check_timesheet_approval_permission(
    db: Session, timesheet: Timesheet, current_user: User
) -> bool:
    """
    检查用户是否有权审批指定的工时记录
    """
    if is_timesheet_admin(current_user):
        return True

    # 不能审批自己的工时（通常业务逻辑如此，如果允许则删掉此行）
    if timesheet.user_id == current_user.id:
        return False

    dims = get_user_manageable_dimensions(db, current_user)

    # 1. 项目经理审批
    if timesheet.project_id and timesheet.project_id in dims["project_ids"]:
        return True

    # 2. 研发项目经理审批
    if timesheet.rd_project_id and timesheet.rd_project_id in dims["rd_project_ids"]:
        return True

    # 3. 部门经理审批
    if timesheet.department_id and timesheet.department_id in dims["department_ids"]:
        return True

    # 4. 直接上级审批
    if timesheet.user_id in dims["subordinate_user_ids"]:
        return True

    return False


def check_bulk_timesheet_approval_permission(
    db: Session, timesheets: List[Timesheet], current_user: User
) -> bool:
    """
    批量检查工时审批权限
    只要其中一条没有权限，则返回 False
    """
    if not timesheets:
        return False

    for ts in timesheets:
        if not check_timesheet_approval_permission(db, ts, current_user):
            return False
    return True


def has_timesheet_approval_access(
    current_user: User,
    db: Session,
    target_user_id: Optional[int] = None,
    target_department_id: Optional[int] = None,
) -> bool:
    """
    检查用户是否有工时审批访问权限（粗粒度）
    """
    if is_timesheet_admin(current_user):
        return True

    dims = get_user_manageable_dimensions(db, current_user)

    # 如果指定了目标用户，检查是否是该用户的经理
    if target_user_id:
        if target_user_id == current_user.id:
            return False  # 不能审批自己的
        if target_user_id in dims["subordinate_user_ids"]:
            return True

        # 还可以通过部门检查
        target_user = db.query(User).filter(User.id == target_user_id).first()
        if target_user and target_user.department_id in dims["department_ids"]:
            return True

    # 如果指定了部门，检查是否是该部门的经理
    if target_department_id:
        if target_department_id in dims["department_ids"]:
            return True

    # 如果没有任何指定，只要是任何一种经理就有权进入审批页面
    if not target_user_id and not target_department_id:
        return any(
            [
                dims["project_ids"],
                dims["rd_project_ids"],
                dims["department_ids"],
                dims["subordinate_user_ids"],
            ]
        )

    return False


def require_timesheet_approval_access():
    """工时审批权限检查依赖"""

    async def timesheet_approval_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(),
    ):
        if not has_timesheet_approval_access(current_user, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有工时审批权限",
            )
        return current_user

    return timesheet_approval_checker
