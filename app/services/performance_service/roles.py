# -*- coding: utf-8 -*-
"""
绩效管理服务 - 角色和权限
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym

from app.models.organization import Department, Employee
from app.models.project import Project, ProjectMember
from app.models.user import User


def get_user_manager_roles(db: Session, user: User) -> Dict[str, Any]:
    """
    判断用户的经理角色

    Returns:
        {
            'is_dept_manager': bool,  # 是否部门经理
            'is_project_manager': bool,  # 是否项目经理
            'managed_dept_id': Optional[int],  # 管理的部门ID
            'managed_project_ids': List[int]  # 管理的项目ID列表
        }
    """
    result = {
        'is_dept_manager': False,
        'is_project_manager': False,
        'managed_dept_id': None,
        'managed_project_ids': []
    }

    # 1. 检查是否是部门经理
    # 查找该用户是否是某个部门的负责人
    # 通过 User.employee_id -> Employee -> Department.manager_id
    if user.employee_id:
        dept = db.query(Department).filter(
            Department.manager_id == user.employee_id,
            Department.is_active
        ).first()

        if dept:
            result['is_dept_manager'] = True
            result['managed_dept_id'] = dept.id

    # 2. 检查是否是项目经理
    # 查找该用户作为PM的所有活跃项目
    managed_projects = db.query(Project).filter(
        Project.pm_id == user.id,
        Project.is_active
    ).all()

    if managed_projects:
        result['is_project_manager'] = True
        result['managed_project_ids'] = [p.id for p in managed_projects]

    return result


def get_manageable_employees(
    db: Session,
    user: User,
    period: Optional[str] = None
) -> List[int]:
    """
    获取经理可以评价的员工ID列表

    Args:
        db: 数据库会话
        user: 当前用户
        period: 评价周期 (YYYY-MM)，用于筛选该周期活跃的项目成员

    Returns:
        员工ID列表
    """
    roles = get_user_manager_roles(db, user)
    employee_ids = set()

    # 1. 如果是部门经理，获取部门下所有员工
    if roles['is_dept_manager'] and roles['managed_dept_id']:
        # 通过 Department -> Employee -> User 获取部门员工
        dept = db.query(Department).get(roles['managed_dept_id'])
        if dept:
            # 查找该部门的所有员工
            employees = db.query(Employee).filter(
                Employee.department == dept.dept_name,  # 使用字符串字段匹配
                Employee.is_active
            ).all()

            # 通过员工ID找到对应的用户
            for emp in employees:
                user_obj = db.query(User).filter(
                    User.employee_id == emp.id,
                    User.is_active
                ).first()
                if user_obj:
                    employee_ids.add(user_obj.id)

    # 2. 如果是项目经理，获取项目成员
    if roles['is_project_manager'] and roles['managed_project_ids']:
        query = db.query(ProjectMember).filter(
            ProjectMember.project_id.in_(roles['managed_project_ids']),
            ProjectMember.is_active
        )

        # 如果指定了周期，只查询该周期内活跃的成员
        if period:
            # 将 YYYY-MM 转换为日期范围
            year, month = map(int, period.split('-'))
            period_start, period_end = get_month_range_by_ym(year, month)

            query = query.filter(
                or_(
                    ProjectMember.start_date.is_(None),
                    ProjectMember.start_date <= period_end
                ),
                or_(
                    ProjectMember.end_date.is_(None),
                    ProjectMember.end_date >= period_start
                )
            )

        members = query.all()
        employee_ids.update([m.user_id for m in members])

    return list(employee_ids)
