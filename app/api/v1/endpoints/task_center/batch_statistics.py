# -*- coding: utf-8 -*-
"""
批量操作 - 统计功能

包含批量操作统计
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.query_filters import apply_like_filter
from app.core import security
from app.models.task_center import TaskOperationLog
from app.models.user import User
from app.schemas.task_center import BatchOperationStatistics

router = APIRouter()


@router.get("/batch/statistics", response_model=BatchOperationStatistics, status_code=status.HTTP_200_OK)
def get_batch_operation_statistics(
    *,
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量操作统计（操作历史）
    """
    query = db.query(TaskOperationLog).filter(
        TaskOperationLog.operator_id == current_user.id,
    )
    query = apply_like_filter(
        query,
        TaskOperationLog,
        "BATCH_%",
        "operation_type",
        use_ilike=False,
    )

    if start_date:
        start_date_str = start_date.strftime("%Y-%m-%d")
        query = query.filter(func.date(TaskOperationLog.operation_time) >= start_date_str)
    if end_date:
        end_date_str = end_date.strftime("%Y-%m-%d")
        query = query.filter(func.date(TaskOperationLog.operation_time) <= end_date_str)

    logs = query.order_by(desc(TaskOperationLog.operation_time)).all()

    # 按操作类型统计
    by_operation_type = {}
    for log in logs:
        op_type = log.operation_type.replace("BATCH_", "")
        by_operation_type[op_type] = by_operation_type.get(op_type, 0) + 1

    # 按日期统计
    by_date = {}
    for log in logs:
        date_str = log.operation_time.date().isoformat()
        by_date[date_str] = by_date.get(date_str, 0) + 1

    # 最近操作
    recent_operations = []
    for log in logs[:20]:  # 最近20条
        recent_operations.append({
            "operation_type": log.operation_type,
            "operation_desc": log.operation_desc,
            "operation_time": log.operation_time.isoformat(),
            "task_id": log.task_id
        })

    return BatchOperationStatistics(
        total_operations=len(logs),
        by_operation_type=by_operation_type,
        by_date=by_date,
        recent_operations=recent_operations
    )
