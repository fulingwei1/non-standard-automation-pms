# -*- coding: utf-8 -*-
"""
工时记录管理 - 自动生成
从 timesheet.py 拆分

工时管理详细 API endpoints
核心功能：周工时表、批量填报、审批流程
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.timesheet import (
    TimesheetBatchCreate,
    TimesheetCreate,
    TimesheetListResponse,
    TimesheetResponse,
    TimesheetUpdate,
)
from app.services.timesheet_records import TimesheetRecordsService

router = APIRouter(prefix="/records", tags=["records"])

# 共 6 个路由

# ==================== 工时记录管理 ====================


@router.get("", response_model=TimesheetListResponse, status_code=status.HTTP_200_OK)
def list_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    pagination=Depends(get_pagination_query),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    工时记录列表（分页+筛选）
    """
    service = TimesheetRecordsService(db)
    items, total = service.list_timesheets(
        current_user=current_user,
        offset=pagination.offset,
        limit=pagination.limit,
        user_id=user_id,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
    )

    return TimesheetListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post("", response_model=TimesheetResponse, status_code=status.HTTP_201_CREATED)
def create_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_in: TimesheetCreate,
    current_user: User = Depends(security.require_permission("timesheet:create")),
) -> Any:
    """
    创建单条工时
    """
    service = TimesheetRecordsService(db)
    return service.create_timesheet(timesheet_in, current_user)


@router.post(
    "/batch", response_model=ResponseModel, status_code=status.HTTP_201_CREATED
)
def batch_create_timesheets(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: TimesheetBatchCreate,
    current_user: User = Depends(security.require_permission("timesheet:create")),
) -> Any:
    """
    批量创建工时
    """
    service = TimesheetRecordsService(db)
    result = service.batch_create_timesheets(batch_in.timesheets, current_user)

    return ResponseModel(
        code=200,
        message=f"批量创建完成：成功 {result['success_count']} 条，失败 {result['failed_count']} 条",
        data=result,
    )


@router.get(
    "/{timesheet_id}", response_model=TimesheetResponse, status_code=status.HTTP_200_OK
)
def get_timesheet_detail(
    timesheet_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取工时记录详情
    """
    service = TimesheetRecordsService(db)
    return service.get_timesheet_detail(timesheet_id, current_user)


@router.put(
    "/{timesheet_id}", response_model=TimesheetResponse, status_code=status.HTTP_200_OK
)
def update_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    timesheet_in: TimesheetUpdate,
    current_user: User = Depends(security.require_permission("timesheet:update")),
) -> Any:
    """
    更新工时记录
    """
    service = TimesheetRecordsService(db)
    return service.update_timesheet(timesheet_id, timesheet_in, current_user)


@router.delete(
    "/{timesheet_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def delete_timesheet(
    *,
    db: Session = Depends(deps.get_db),
    timesheet_id: int,
    current_user: User = Depends(security.require_permission("timesheet:delete")),
) -> Any:
    """
    删除工时记录（仅草稿）
    """
    service = TimesheetRecordsService(db)
    service.delete_timesheet(timesheet_id, current_user)

    return ResponseModel(message="工时记录已删除")
