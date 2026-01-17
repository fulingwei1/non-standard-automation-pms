# -*- coding: utf-8 -*-
"""
项目成员冲突检查
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectMember
from app.models.user import User

router = APIRouter()


def check_member_conflicts_internal(
    db: Session,
    user_id: int,
    start_date: Optional[date],
    end_date: Optional[date],
    exclude_project_id: Optional[int] = None
) -> dict:
    """
    检查成员分配冲突（内部函数）

    Returns:
        冲突信息字典
    """
    if not start_date or not end_date:
        return {'has_conflict': False}

    # 查询该用户在同一时间段的其他项目分配
    query = db.query(ProjectMember).filter(
        ProjectMember.user_id == user_id,
        ProjectMember.is_active == True,
        or_(
            # 新分配的开始日期在现有分配的时间范围内
            and_(
                ProjectMember.start_date <= start_date,
                ProjectMember.end_date >= start_date
            ),
            # 新分配的结束日期在现有分配的时间范围内
            and_(
                ProjectMember.start_date <= end_date,
                ProjectMember.end_date >= end_date
            ),
            # 新分配完全包含现有分配
            and_(
                ProjectMember.start_date >= start_date,
                ProjectMember.end_date <= end_date
            )
        )
    )

    if exclude_project_id:
        query = query.filter(ProjectMember.project_id != exclude_project_id)

    conflicting_members = query.all()

    if not conflicting_members:
        return {'has_conflict': False}

    # 获取冲突的项目信息
    conflicting_projects = []
    for member in conflicting_members:
        project = db.query(Project).filter(Project.id == member.project_id).first()
        if project:
            conflicting_projects.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.project_name,
                'allocation_pct': float(member.allocation_pct or 100),
                'start_date': member.start_date.isoformat() if member.start_date else None,
                'end_date': member.end_date.isoformat() if member.end_date else None,
            })

    user = db.query(User).filter(User.id == user_id).first()
    user_name = user.real_name or user.username if user else f'User {user_id}'

    return {
        'has_conflict': True,
        'user_id': user_id,
        'user_name': user_name,
        'conflicting_projects': conflicting_projects,
        'conflict_count': len(conflicting_projects)
    }


@router.get("/projects/{project_id}/members/conflicts", response_model=dict)
def check_member_conflicts(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    user_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    检查成员分配冲突
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    check_project_access_or_raise(db, current_user, project_id)

    conflict_info = check_member_conflicts_internal(
        db, user_id, start_date, end_date, project_id
    )

    return conflict_info
