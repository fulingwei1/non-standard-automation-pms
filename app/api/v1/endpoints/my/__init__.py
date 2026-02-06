# -*- coding: utf-8 -*-
"""
个人维度 API 模块

提供当前用户视角的聚合数据：
- /my/projects    我参与的项目
- /my/workload    我的工作量摘要
- /my/timesheet   我的工时记录
- /my/tasks       我的任务列表
- /my/work-logs   我的工作日志
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.task_center import TaskUnified
from app.models.timesheet import Timesheet
from app.models.user import User
from app.models.work_log import WorkLog
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.engineer import MyProjectListResponse, TaskResponse
from app.schemas.timesheet import TimesheetResponse
from app.schemas.work_log import WorkLogListResponse, WorkLogResponse
from app.schemas.workload import UserWorkloadResponse
from app.services.project import ProjectCoreService, ProjectResourceService

router = APIRouter()


@router.get("/projects", response_model=ResponseModel[MyProjectListResponse])
def get_my_projects(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """我参与的项目列表"""
    service = ProjectCoreService(db)
    data = service.list_user_projects(current_user, page=page, page_size=page_size)
    return ResponseModel(data=data)


@router.get("/workload", response_model=ResponseModel[UserWorkloadResponse])
def get_my_workload(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """我的工作量摘要"""
    service = ProjectResourceService(db)
    data = service.get_user_workload(current_user.id, start_date, end_date)
    return ResponseModel(data=data)


@router.get("/timesheet", response_model=ResponseModel[PaginatedResponse[TimesheetResponse]])
def get_my_timesheets(
    pagination=Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """我的工时记录"""
    query = db.query(Timesheet).filter(Timesheet.user_id == current_user.id)
    if status:
        query = query.filter(Timesheet.status == status)
    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    total = query.count()
    query = query.order_by(Timesheet.work_date.desc(), Timesheet.id.desc())
    query = apply_pagination(query, pagination.offset, pagination.limit)
    items = query.all()
    payload = PaginatedResponse(
        items=[TimesheetResponse.model_validate(item) for item in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )
    return ResponseModel(data=payload)


@router.get("/tasks", response_model=ResponseModel[PaginatedResponse[TaskResponse]])
def get_my_tasks(
    pagination=Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="任务标题关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """我的任务列表"""
    query = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == current_user.id,
        TaskUnified.is_active == True,  # noqa: E712
    )
    if status:
        query = query.filter(TaskUnified.status == status)
    query = apply_keyword_filter(query, TaskUnified, keyword, "title")

    total = query.count()
    query = query.order_by(TaskUnified.updated_at.desc().nullslast(), TaskUnified.id.desc())
    query = apply_pagination(query, pagination.offset, pagination.limit)
    items = query.all()
    payload = PaginatedResponse(
        items=[TaskResponse.model_validate(task) for task in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )
    return ResponseModel(data=payload)


@router.get("/work-logs", response_model=ResponseModel[WorkLogListResponse])
def get_my_work_logs(
    pagination=Depends(get_pagination_query),
    start_date: Optional[date] = Query(None, description="起始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """我的工作日志"""
    query = db.query(WorkLog).filter(WorkLog.user_id == current_user.id)
    if start_date:
        query = query.filter(WorkLog.work_date >= start_date)
    if end_date:
        query = query.filter(WorkLog.work_date <= end_date)

    total = query.count()
    query = query.order_by(WorkLog.work_date.desc(), WorkLog.id.desc())
    query = apply_pagination(query, pagination.offset, pagination.limit)
    items = query.all()
    payload = WorkLogListResponse(
        items=[WorkLogResponse.model_validate(log) for log in items],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )
    return ResponseModel(data=payload)
