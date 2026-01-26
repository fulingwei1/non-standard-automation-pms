# -*- coding: utf-8 -*-
"""
更新任务进度 - 自动生成
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

from .detail import get_task_detail

router = APIRouter()

# 使用统一的编码生成工具和日志工具
from .batch_helpers import generate_task_code, log_task_operation


from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/update",
    tags=["update"]
)

# 共 1 个路由

# ==================== 更新任务进度 ====================

@router.put("/tasks/{task_id}/progress", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress_in: TaskProgressUpdate,
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """
    更新任务进度
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权更新此任务")

    old_progress = task.progress
    old_hours = task.actual_hours

    task.progress = progress_in.progress
    if progress_in.actual_hours is not None:
        task.actual_hours = progress_in.actual_hours
    task.updated_by = current_user.id

    # 如果进度为100%，自动完成
    if progress_in.progress >= 100 and task.status != "COMPLETED":
        task.status = "COMPLETED"
        task.actual_end_date = datetime.now().date()

    # 如果开始更新进度且未开始，自动开始
    if progress_in.progress > 0 and task.status == "ACCEPTED":
        task.status = "IN_PROGRESS"
        if not task.actual_start_date:
            task.actual_start_date = datetime.now().date()

    db.add(task)
    db.commit()
    db.refresh(task)

    log_task_operation(
        db, task.id, "UPDATE_PROGRESS",
        f"更新进度：{old_progress}% -> {progress_in.progress}%",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"progress": old_progress, "actual_hours": float(old_hours) if old_hours else 0},
        new_value={"progress": progress_in.progress, "actual_hours": float(progress_in.actual_hours) if progress_in.actual_hours else None}
    )

    return get_task_detail(task_id, db, current_user)


