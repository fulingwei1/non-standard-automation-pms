# -*- coding: utf-8 -*-
"""
项目工时自定义端点（使用统一统计服务）

使用统一统计服务重构，减少代码重复
"""

from datetime import date
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.project_statistics_service import TimesheetStatisticsService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


@router.get("/summary", response_model=ResponseModel)
def get_project_timesheet_summary(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目工时汇总（使用统一统计服务）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = TimesheetStatisticsService(db)
    summary = service.get_summary(project_id, start_date, end_date)
    
    return ResponseModel(
        code=200,
        message="success",
        data=summary,
    )


@router.get("/statistics", response_model=ResponseModel)
def get_project_timesheet_statistics(
    project_id: int = Path(..., description="项目ID"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目工时统计分析（使用统一统计服务）"""
    check_project_access_or_raise(db, current_user, project_id)
    
    service = TimesheetStatisticsService(db)
    statistics = service.get_statistics(project_id, start_date, end_date)
    
    return ResponseModel(
        code=200,
        message="success",
        data=statistics,
    )
