# -*- coding: utf-8 -*-
"""
周工时表 - 自动生成
从 timesheet.py 拆分
"""

# -*- coding: utf-8 -*-
"""
工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.timesheet import (
    Timesheet,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.timesheet import (
    TimesheetResponse,
    WeekTimesheetResponse,
)

router = APIRouter()


from fastapi import APIRouter

router = APIRouter(prefix="/timesheets", tags=["timesheets"])

# 共 1 个路由

# ==================== 周工时表 ====================


@router.get(
    "/week", response_model=WeekTimesheetResponse, status_code=status.HTTP_200_OK
)
def get_week_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    week_start: Optional[date] = Query(None, description="周开始日期（默认本周一）"),
    user_id: Optional[int] = Query(None, description="用户ID（默认当前用户）"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取周工时表（按周展示）
    """
    from app.core.permissions.timesheet import (
        is_timesheet_admin,
        get_user_manageable_dimensions,
    )

    # 获取目标用户ID
    target_user_id = user_id or current_user.id

    # 权限检查
    if target_user_id != current_user.id:
        dims = get_user_manageable_dimensions(db, current_user)
        if not dims["is_admin"] and target_user_id not in dims["subordinate_user_ids"]:
            # 检查是否属于我管理的部门
            target_user = db.query(User).filter(User.id == target_user_id).first()
            if (
                not target_user
                or target_user.department_id not in dims["department_ids"]
            ):
                raise HTTPException(status_code=403, detail="无权查看其他用户的工时")

    # 计算周开始日期
    if not week_start:
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())

    week_end = week_start + timedelta(days=6)

    # 查询该周的工时记录
    timesheets = (
        db.query(Timesheet)
        .filter(
            Timesheet.user_id == target_user_id,
            Timesheet.work_date >= week_start,
            Timesheet.work_date <= week_end,
        )
        .order_by(Timesheet.work_date)
        .all()
    )

    # 按日期统计
    by_date = {}
    total_hours = Decimal("0")
    for ts in timesheets:
        date_str = ts.work_date.isoformat()
        if date_str not in by_date:
            by_date[date_str] = Decimal("0")
        by_date[date_str] += ts.hours or Decimal("0")
        total_hours += ts.hours or Decimal("0")

    # 按项目统计
    by_project = {}
    for ts in timesheets:
        project_name = "未分配项目"
        if ts.project_id:
            project = db.query(Project).filter(Project.id == ts.project_id).first()
            project_name = project.project_name if project else "未知项目"

        if project_name not in by_project:
            by_project[project_name] = Decimal("0")
        by_project[project_name] += ts.hours or Decimal("0")

    # 构建响应
    items = []
    user = db.query(User).filter(User.id == target_user_id).first()
    for ts in timesheets:
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

    return WeekTimesheetResponse(
        week_start=week_start,
        week_end=week_end,
        total_hours=total_hours,
        by_date=by_date,
        by_project=by_project,
        timesheets=items,
    )


@router.post(
    "/week/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def submit_week_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    week_start: date = Body(..., description="周开始日期"),
    current_user: User = Depends(security.require_permission("timesheet:submit")),
) -> Any:
    """
    提交周工时记录
    将指定周的所有草稿状态工时记录提交审批
    """
    week_end = week_start + timedelta(days=6)

    # 查询该周所有草稿状态的工时记录
    timesheets = (
        db.query(Timesheet)
        .filter(
            and_(
                Timesheet.user_id == current_user.id,
                Timesheet.work_date >= week_start,
                Timesheet.work_date <= week_end,
                Timesheet.status == "DRAFT",
            )
        )
        .all()
    )

    if not timesheets:
        return ResponseModel(code=200, message="没有需要提交的工时记录")

    # 更新状态为待审批
    for ts in timesheets:
        ts.status = "PENDING"
        ts.submitted_at = datetime.now()

    db.commit()

    return ResponseModel(code=200, message=f"已提交 {len(timesheets)} 条工时记录")
