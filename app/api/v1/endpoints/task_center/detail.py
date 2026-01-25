# -*- coding: utf-8 -*-
"""
任务详情 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.notification import Notification
from app.models.project import Project
from app.models.task_center import (
    JobDutyTemplate,
    TaskComment,
    TaskOperationLog,
    TaskReminder,
    TaskUnified,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.task_center import (
    BatchOperationResponse,
    BatchOperationStatistics,
    BatchTaskOperation,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskOverviewResponse,
    TaskProgressUpdate,
    TaskTransferRequest,
    TaskUnifiedCreate,
    TaskUnifiedListResponse,
    TaskUnifiedResponse,
    TaskUnifiedUpdate,
)
from app.services.sales_reminder import create_notification

router = APIRouter()

# 使用统一的编码生成工具和日志工具
from .batch_helpers import generate_task_code, log_task_operation


from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/detail",
    tags=["detail"]
)

# 共 1 个路由

# ==================== 任务详情 ====================

@router.get("/tasks/{task_id}", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def get_task_detail(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    任务详情
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 检查权限（只有执行人可以查看）
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此任务")

    today = datetime.now().date()
    is_overdue = False
    if task.deadline and task.status in ["PENDING", "ACCEPTED", "IN_PROGRESS"]:
        deadline_date = task.deadline.date() if isinstance(task.deadline, datetime) else task.deadline
        if deadline_date < today:
            is_overdue = True

    return TaskUnifiedResponse(
        id=task.id,
        task_code=task.task_code,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        source_type=task.source_type,
        source_id=task.source_id,
        source_name=task.source_name,
        project_id=task.project_id,
        project_name=task.project_name,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee_name,
        assigner_id=task.assigner_id,
        assigner_name=task.assigner_name,
        plan_start_date=task.plan_start_date,
        plan_end_date=task.plan_end_date,
        actual_start_date=task.actual_start_date,
        actual_end_date=task.actual_end_date,
        deadline=task.deadline,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours or Decimal("0"),
        status=task.status,
        progress=task.progress or 0,
        priority=task.priority,
        is_urgent=task.is_urgent or False,
        is_transferred=task.is_transferred or False,
        transfer_from_name=task.transfer_from_name,
        tags=task.tags if task.tags else [],
        category=task.category,
        is_overdue=is_overdue,
        created_at=task.created_at,
        updated_at=task.updated_at
    )



