# -*- coding: utf-8 -*-
"""
项目工时 CRUD 操作（重构版本）

使用项目中心CRUD路由基类，大幅减少代码量
复杂逻辑通过覆盖端点实现
"""

from datetime import date
from decimal import Decimal
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.v1.core.project_crud_base import create_project_crud_router
from app.api import deps
from app.common.pagination import get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.schemas.timesheet import (
    TimesheetCreate,
    TimesheetUpdate,
    TimesheetResponse,
    TimesheetListResponse,
)
from app.utils.permission_helpers import check_project_access_or_raise


def filter_by_user(query, user_id: int):
    """自定义用户筛选器"""
    return query.filter(Timesheet.user_id == user_id)


def filter_by_status(query, status: str):
    """自定义状态筛选器"""
    return query.filter(Timesheet.status == status)


def _map_timesheet_fields(item_data: dict, project_id: int, current_user) -> dict:
    """将 schema 字段映射为 model 字段"""
    if "work_hours" in item_data:
        item_data["hours"] = item_data.pop("work_hours")
    if "work_type" in item_data:
        item_data["overtime_type"] = item_data.pop("work_type")
    if "description" in item_data:
        item_data["work_content"] = item_data.pop("description")
    # 移除 model 不存在的字段
    item_data.pop("is_billable", None)
    # 设置 user_id
    if "user_id" not in item_data or item_data["user_id"] is None:
        item_data["user_id"] = current_user.id
    return item_data


# 使用项目中心CRUD路由基类创建路由
base_router = create_project_crud_router(
    model=Timesheet,
    create_schema=TimesheetCreate,
    update_schema=TimesheetUpdate,
    response_schema=TimesheetResponse,
    permission_prefix="project",
    project_id_field="project_id",
    keyword_fields=["work_content", "work_result"],
    default_order_by="work_date",
    default_order_direction="desc",
    custom_filters={
        "user_id": filter_by_user,  # 支持 ?user_id=1 筛选
        "status": filter_by_status,  # 支持 ?status=APPROVED 筛选
    },
    before_create=_map_timesheet_fields,
)

# 创建新的router
router = APIRouter()

# 先包含 base_router（包含所有 CRUD 端点）
# 然后我们会覆盖 GET / 和 GET /{id} 端点
router.include_router(base_router)


def enrich_timesheet_response(ts: Timesheet, db: Session, project: Project) -> TimesheetResponse:
    """填充工时记录的user_name、project_name、task_name"""
    user = db.query(User).filter(User.id == ts.user_id).first()
    
    task_name = None
    if ts.task_id:
        from app.models.progress import Task
        task = db.query(Task).filter(Task.id == ts.task_id).first()
        task_name = task.task_name if task else None
    
    return TimesheetResponse(
        id=ts.id,
        user_id=ts.user_id,
        user_name=user.real_name or user.username if user else None,
        project_id=ts.project_id,
        rd_project_id=ts.rd_project_id,
        project_name=project.project_name,
        task_id=ts.task_id,
        task_name=task_name,
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


# 覆盖列表端点，填充用户信息和任务名称
@router.get("/", response_model=TimesheetListResponse)
def list_project_timesheets(
    project_id: int = Path(..., description="项目ID"),
    pagination=Depends(get_pagination_query),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    status: Optional[str] = Query(None, alias="status_filter", description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目的所有工时记录（覆盖基类端点，填充用户信息和任务名称）"""
    check_project_access_or_raise(db, current_user, project_id)

    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(Timesheet).filter(Timesheet.project_id == project_id)

    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)
    if user_id:
        query = query.filter(Timesheet.user_id == user_id)
    if status:
        query = query.filter(Timesheet.status == status)

    total = query.count()
    query = query.order_by(desc(Timesheet.work_date), desc(Timesheet.created_at))
    query = apply_pagination(query, pagination.offset, pagination.limit)
    timesheets = query.all()

    # 填充用户信息和任务名称
    items = [enrich_timesheet_response(ts, db, project) for ts in timesheets]

    return TimesheetListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


# 覆盖详情端点，填充用户信息和任务名称
@router.get("/{timesheet_id}", response_model=TimesheetResponse)
def get_project_timesheet(
    project_id: int = Path(..., description="项目ID"),
    timesheet_id: int = Path(..., description="工时记录ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取工时记录详情（覆盖基类端点，填充用户信息和任务名称）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    # 验证项目存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    timesheet = db.query(Timesheet).filter(
        Timesheet.id == timesheet_id,
        Timesheet.project_id == project_id,
    ).first()
    
    if not timesheet:
        raise HTTPException(status_code=404, detail="工时记录不存在")
    
    return enrich_timesheet_response(timesheet, db, project)
