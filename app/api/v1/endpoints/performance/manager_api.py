# -*- coding: utf-8 -*-
"""
新绩效-经理端 - 自动生成
从 performance.py 拆分
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.performance import (
    EvaluationDetailResponse,
    EvaluationTaskListResponse,
    PerformanceEvaluationRecordCreate,
    PerformanceEvaluationRecordResponse,
)
from app.services.manager_performance import ManagerPerformanceService

router = APIRouter(prefix="/performance/new/manager", tags=["manager_api"])


@router.get(
    "/evaluation-tasks",
    response_model=EvaluationTaskListResponse,
    status_code=status.HTTP_200_OK,
)
def get_evaluation_tasks(
    *,
    db: Session = Depends(deps.get_db),
    period: Optional[str] = Query(None, description="评价周期 (YYYY-MM)"),
    status_filter: Optional[str] = Query(None, description="状态筛选: PENDING/COMPLETED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理查看待评价任务列表（带权限过滤）
    """
    service = ManagerPerformanceService(db)
    result = service.get_evaluation_tasks(current_user, period, status_filter)

    return EvaluationTaskListResponse(
        total=result["total"],
        pending_count=result["pending_count"],
        completed_count=result["completed_count"],
        tasks=result["tasks"],
    )


@router.get(
    "/evaluation/{task_id}",
    response_model=EvaluationDetailResponse,
    status_code=status.HTTP_200_OK,
)
def get_evaluation_detail(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理查看评价详情（工作总结+历史绩效）
    """
    service = ManagerPerformanceService(db)

    try:
        result = service.get_evaluation_detail(current_user, task_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return EvaluationDetailResponse(
        summary=result["summary"],
        employee_info=result["employee_info"],
        historical_performance=result["historical_performance"],
        my_evaluation=result["my_evaluation"],
    )


@router.post(
    "/evaluation/{task_id}",
    response_model=PerformanceEvaluationRecordResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_evaluation(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    evaluation_in: PerformanceEvaluationRecordCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    经理提交评价
    """
    service = ManagerPerformanceService(db)

    try:
        evaluation = service.submit_evaluation(current_user, task_id, evaluation_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return evaluation
