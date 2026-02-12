# -*- coding: utf-8 -*-
"""
工程师项目管理 API 端点
包含：我的项目列表查询
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.project import Project, ProjectMember
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas import engineer as schemas
from app.common.query_filters import apply_pagination

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/my-projects", response_model=schemas.MyProjectListResponse)
def get_my_projects(
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取工程师参与的所有项目（含任务统计）
    """
    # 查询用户参与的项目
    project_members = db.query(ProjectMember).filter(
        and_(
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active
        )
    ).all()

    project_ids = [pm.project_id for pm in project_members]

    # 分页查询项目
    query = db.query(Project).filter(Project.id.in_(project_ids))
    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        total = 0

    projects = apply_pagination(query, pagination.offset, pagination.limit).all()

    # 构建响应
    items = []
    for project in projects:
        # 获取我的角色
        my_roles = [pm.role_code for pm in project_members if pm.project_id == project.id]
        my_allocation = next((pm.allocation_pct for pm in project_members if pm.project_id == project.id), 100)

        # 统计我的任务
        my_tasks = db.query(TaskUnified).filter(
            and_(
                TaskUnified.project_id == project.id,
                TaskUnified.assignee_id == current_user.id
            )
        ).all()

        task_stats = schemas.TaskStatsResponse(
            total_tasks=len(my_tasks),
            pending_tasks=len([t for t in my_tasks if t.status == 'PENDING']),
            in_progress_tasks=len([t for t in my_tasks if t.status == 'IN_PROGRESS']),
            completed_tasks=len([t for t in my_tasks if t.status == 'COMPLETED']),
            overdue_tasks=len([t for t in my_tasks if t.deadline and t.deadline < datetime.now()
                              and t.status not in ['COMPLETED', 'CANCELLED']]),
            delayed_tasks=len([t for t in my_tasks if t.is_delayed]),
            pending_approval_tasks=len([t for t in my_tasks if t.approval_status == 'PENDING_APPROVAL'])
        )

        # 获取客户名称
        customer_name = project.customer.customer_name if project.customer else None

        items.append(schemas.MyProjectResponse(
            project_id=project.id,
            project_code=project.project_code,
            project_name=project.project_name,
            customer_name=customer_name,
            stage=project.stage,
            status=project.status,
            health=project.health,
            progress_pct=float(project.progress_pct) if project.progress_pct else 0.0,
            my_roles=my_roles,
            my_allocation_pct=my_allocation,
            task_stats=task_stats,
            planned_start_date=project.planned_start_date,
            planned_end_date=project.planned_end_date,
            last_activity_at=project.updated_at
        ))

    return schemas.MyProjectListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )
