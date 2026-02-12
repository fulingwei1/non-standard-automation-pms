# -*- coding: utf-8 -*-
"""
任务概览 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.task_center import (
    TaskUnified,
)
from app.models.user import User
from app.schemas.task_center import (
    TaskOverviewResponse,
)

router = APIRouter()

# 使用统一的编码生成工具和日志工具


from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/overview",
    tags=["overview"]
)

# 共 1 个路由

# ==================== 任务概览 ====================

@router.get("/overview", response_model=TaskOverviewResponse, status_code=status.HTTP_200_OK)
def get_task_overview(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    任务概览统计（待办/逾期/本周）
    """
    user_id = current_user.id
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())

    # 总任务数
    total_tasks = db.query(TaskUnified).filter(TaskUnified.assignee_id == user_id).count()

    # 待接收任务（转办任务）
    pending_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status == "PENDING"
    ).count()

    # 进行中任务
    in_progress_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status == "IN_PROGRESS"
    ).count()

    # 逾期任务
    today_str = today.strftime("%Y-%m-%d")
    overdue_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"]),
        TaskUnified.deadline.isnot(None),
        func.date(TaskUnified.deadline) < today_str
    ).count()

    # 本周任务
    this_week_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.plan_start_date >= week_start,
        TaskUnified.plan_start_date <= week_start + timedelta(days=6)
    ).count()

    # 紧急任务
    urgent_tasks = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == user_id,
        TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"]),
        or_(TaskUnified.is_urgent, TaskUnified.priority == "URGENT")
    ).count()

    # 按状态统计
    status_stats = {}
    status_counts = (
        db.query(TaskUnified.status, func.count(TaskUnified.id))
        .filter(TaskUnified.assignee_id == user_id)
        .group_by(TaskUnified.status)
        .all()
    )
    for status, count in status_counts:
        status_stats[status] = count

    # 按优先级统计
    priority_stats = {}
    priority_counts = (
        db.query(TaskUnified.priority, func.count(TaskUnified.id))
        .filter(TaskUnified.assignee_id == user_id)
        .group_by(TaskUnified.priority)
        .all()
    )
    for priority, count in priority_counts:
        priority_stats[priority] = count

    # 按类型统计
    type_stats = {}
    type_counts = (
        db.query(TaskUnified.task_type, func.count(TaskUnified.id))
        .filter(TaskUnified.assignee_id == user_id)
        .group_by(TaskUnified.task_type)
        .all()
    )
    for task_type, count in type_counts:
        type_stats[task_type] = count

    return TaskOverviewResponse(
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        overdue_tasks=overdue_tasks,
        this_week_tasks=this_week_tasks,
        urgent_tasks=urgent_tasks,
        by_status=status_stats,
        by_priority=priority_stats,
        by_type=type_stats
    )



