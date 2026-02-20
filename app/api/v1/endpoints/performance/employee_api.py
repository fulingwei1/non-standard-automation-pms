# -*- coding: utf-8 -*-
"""
新绩效-员工端 - 重构版本
从 performance.py 拆分，业务逻辑已提取到服务层
"""

from typing import Any, List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.performance import (
    MonthlyWorkSummaryCreate,
    MonthlyWorkSummaryListItem,
    MonthlyWorkSummaryResponse,
    MonthlyWorkSummaryUpdate,
    MyPerformanceResponse,
)
from app.services.employee_performance import EmployeePerformanceService

router = APIRouter(prefix="/performance/new/employee", tags=["employee_api"])


@router.post(
    "/monthly-summary",
    response_model=MonthlyWorkSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_monthly_work_summary(
    *,
    db: Session = Depends(deps.get_db),
    summary_in: MonthlyWorkSummaryCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工创建月度工作总结（提交）
    """
    service = EmployeePerformanceService(db)
    return service.create_monthly_work_summary(current_user, summary_in)


@router.put(
    "/monthly-summary/draft",
    response_model=MonthlyWorkSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def save_monthly_summary_draft(
    *,
    db: Session = Depends(deps.get_db),
    period: str = Query(..., description="评价周期 (YYYY-MM)"),
    summary_update: MonthlyWorkSummaryUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工保存工作总结草稿
    """
    service = EmployeePerformanceService(db)
    return service.save_monthly_summary_draft(current_user, period, summary_update)


@router.get(
    "/monthly-summary/history",
    response_model=List[MonthlyWorkSummaryListItem],
    status_code=status.HTTP_200_OK,
)
def get_monthly_summary_history(
    *,
    db: Session = Depends(deps.get_db),
    limit: int = Query(12, ge=1, le=24, description="获取最近N个月"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工查看历史工作总结
    """
    service = EmployeePerformanceService(db)
    return service.get_monthly_summary_history(current_user, limit)


@router.get(
    "/my-performance",
    response_model=MyPerformanceResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_performance_new(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    员工查看我的绩效（新系统）
    """
    service = EmployeePerformanceService(db)
    return service.get_my_performance(current_user)
