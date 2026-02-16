# -*- coding: utf-8 -*-
"""
待审核列表 - 自动生成
从 timesheet.py 拆分
"""

# -*- coding: utf-8 -*-
"""
工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.timesheet import (
    Timesheet,
)
from app.models.project import Project
from app.models.user import User
from app.schemas.timesheet import (
    TimesheetListResponse,
    TimesheetResponse,
)
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


from fastapi import APIRouter
from app.common.query_filters import apply_pagination

router = APIRouter(prefix="/pending", tags=["pending"])

# 共 1 个路由

# ==================== 待审核列表 ====================


@router.get(
    "/pending-approval",
    response_model=TimesheetListResponse,
    status_code=status.HTTP_200_OK,
)
def get_pending_approval_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    待审核列表（审核人视角）
    只返回当前用户有权审批的工时记录
    """
    # 过滤出用户有权限审批的工时记录
    # 项目经理只能看到本项目的工时，部门经理只能看到本部门的工时
    from app.core.permissions.timesheet import apply_timesheet_access_filter

    query = db.query(Timesheet).filter(Timesheet.status == "PENDING")
    query = apply_timesheet_access_filter(query, db, current_user)

    if user_id:
        query = query.filter(Timesheet.user_id == user_id)
    if project_id:
        query = query.filter(Timesheet.project_id == project_id)

    total = query.count()
    timesheets = (
        apply_pagination(query.order_by(Timesheet.work_date.desc()), pagination.offset, pagination.limit).all()
    )

    items = []
    for ts in timesheets:
        user = db.query(User).filter(User.id == ts.user_id).first()
        project = None
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()

        items.append(
            TimesheetResponse(
                id=ts.id,
                user_id=ts.user_id,
                user_name=user.real_name or user.username if user else None,
                project_id=ts.project_id,
                rd_project_id=ts.rd_project_id,
                project_name=project.project_name if project else None,
                task_id=ts.task_id,
                task_name=None,
                work_date=ts.work_date,
                work_hours=ts.hours or Decimal("0"),
                work_type=ts.overtime_type or "NORMAL",
                description=ts.work_content,
                status=ts.status or "DRAFT",
                approved_by=ts.approver_id,
                approved_at=ts.approve_time,
                created_at=ts.created_at,
                updated_at=ts.updated_at,
            )
        )

    return TimesheetListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )
