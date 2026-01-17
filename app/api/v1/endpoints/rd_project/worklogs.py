# -*- coding: utf-8 -*-
"""
研发项目工作日志管理
"""
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.rd_project import RdProject
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.timesheet import (
    TimesheetCreate,
    TimesheetListResponse,
    TimesheetResponse,
)

router = APIRouter()

# ==================== 研发项目工作日志 ====================

# 共 2 个路由

# ==================== 研发项目工作日志 ====================

@router.get("/rd-projects/{project_id}/worklogs", response_model=ResponseModel)
def get_rd_project_worklogs(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    获取研发项目工作日志列表
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    offset = (page - 1) * page_size
    query = db.query(Timesheet).filter(Timesheet.rd_project_id == project_id)

    if user_id:
        query = query.filter(Timesheet.user_id == user_id)
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)
    if status:
        query = query.filter(Timesheet.status == status)

    total = query.count()
    timesheets = query.order_by(desc(Timesheet.work_date), desc(Timesheet.created_at)).offset(offset).limit(page_size).all()

    items = []
    for ts in timesheets:
        items.append(TimesheetResponse(
            id=ts.id,
            user_id=ts.user_id,
            user_name=ts.user_name,
            project_id=ts.project_id,
            project_name=ts.project_name,
            task_id=ts.task_id,
            task_name=ts.task_name,
            work_date=ts.work_date,
            work_hours=ts.hours or Decimal("0"),
            work_type=ts.overtime_type or "NORMAL",
            description=ts.work_content,
            is_billable=True,
            status=ts.status or "DRAFT",
            approved_by=ts.approver_id,
            approved_at=ts.approve_time,
            created_at=ts.created_at,
            updated_at=ts.updated_at
        ))

    return ResponseModel(
        code=200,
        message="success",
        data=TimesheetListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
    )


@router.post("/rd-projects/{project_id}/worklogs", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_rd_project_worklog(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    worklog_in: TimesheetCreate,
    current_user: User = Depends(security.require_rd_project_access),
) -> Any:
    """
    创建研发项目工作日志
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    # 检查同一天是否已有记录
    existing = db.query(Timesheet).filter(
        Timesheet.user_id == current_user.id,
        Timesheet.work_date == worklog_in.work_date,
        Timesheet.rd_project_id == project_id,
        Timesheet.status != "REJECTED"
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该日期已有工作日志记录，请更新或删除后重试")

    timesheet = Timesheet(
        user_id=current_user.id,
        user_name=current_user.name,
        rd_project_id=project_id,
        project_id=project.linked_project_id,  # 如果有关联的非标项目，也记录
        project_name=project.project_name,
        work_date=worklog_in.work_date,
        hours=worklog_in.work_hours,
        overtime_type=worklog_in.work_type,
        work_content=worklog_in.description,
        status="DRAFT",
        created_by=current_user.id
    )

    db.add(timesheet)
    db.commit()
    db.refresh(timesheet)

    return ResponseModel(
        code=201,
        message="工作日志创建成功",
        data=TimesheetResponse(
            id=timesheet.id,
            user_id=timesheet.user_id,
            user_name=timesheet.user_name,
            project_id=timesheet.project_id,
            project_name=timesheet.project_name,
            task_id=timesheet.task_id,
            task_name=timesheet.task_name,
            work_date=timesheet.work_date,
            work_hours=timesheet.hours or Decimal("0"),
            work_type=timesheet.overtime_type or "NORMAL",
            description=timesheet.work_content,
            is_billable=True,
            status=timesheet.status or "DRAFT",
            approved_by=timesheet.approver_id,
            approved_at=timesheet.approve_time,
            created_at=timesheet.created_at,
            updated_at=timesheet.updated_at
        )
    )



