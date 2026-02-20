# -*- coding: utf-8 -*-
"""
项目绩效 - 自动生成
从 performance.py 拆分
重构：业务逻辑已提取到 app.services.project_performance.ProjectPerformanceService
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.performance import (
    PerformanceCompareResponse,
    ProjectPerformanceResponse,
    ProjectProgressReportResponse,
)
from app.services.project_performance import ProjectPerformanceService

router = APIRouter(prefix="/performance/project", tags=["project"])


# ==================== 项目绩效 ====================


@router.get(
    "/project/{project_id}",
    response_model=ProjectPerformanceResponse,
    status_code=status.HTTP_200_OK,
)
def get_project_performance(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目成员绩效（项目贡献）
    """
    service = ProjectPerformanceService(db)
    try:
        result = service.get_project_performance(project_id, period_id)
        return ProjectPerformanceResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/project/{project_id}/progress",
    response_model=ProjectProgressReportResponse,
    status_code=status.HTTP_200_OK,
)
def get_project_progress_report(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    report_type: str = Query("WEEKLY", description="报告类型：WEEKLY/MONTHLY"),
    report_date: Optional[date] = Query(None, description="报告日期（默认今天）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目进展报告（周报/月报）
    """
    service = ProjectPerformanceService(db)
    try:
        result = service.get_project_progress_report(
            project_id, report_type, report_date
        )
        return ProjectProgressReportResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/compare",
    response_model=PerformanceCompareResponse,
    status_code=status.HTTP_200_OK,
)
def compare_performance(
    *,
    db: Session = Depends(deps.get_db),
    user_ids: str = Query(..., description="用户ID列表，逗号分隔"),
    period_id: Optional[int] = Query(None, description="周期ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    绩效对比（多人对比）
    """
    user_id_list = [int(uid.strip()) for uid in user_ids.split(",") if uid.strip()]

    service = ProjectPerformanceService(db)
    try:
        result = service.compare_performance(user_id_list, period_id)
        return PerformanceCompareResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
