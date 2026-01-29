# -*- coding: utf-8 -*-
"""
绩效评价任务 API
提供评价任务列表查询功能
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.performance import EvaluationTaskListResponse

router = APIRouter(
    prefix="/performance",
    tags=["performance-evaluation-tasks"]
)


@router.get("/evaluation-tasks", response_model=EvaluationTaskListResponse, status_code=status.HTTP_200_OK)
def get_evaluation_tasks(
    *,
    db: Session = Depends(deps.get_db),
    period: Optional[str] = Query(None, description="评价周期 (YYYY-MM)"),
    status_filter: Optional[str] = Query(None, description="状态筛选: PENDING/COMPLETED"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取评价任务列表

    返回当前用户的评价任务列表（暂时返回空列表）
    """
    if not period:
        period = date.today().strftime("%Y-%m")

    # 暂时返回空列表，避免前端报错
    # TODO: 实现完整的评价任务查询逻辑
    return EvaluationTaskListResponse(
        tasks=[],
        total=0,
        pending_count=0,
        completed_count=0
    )
