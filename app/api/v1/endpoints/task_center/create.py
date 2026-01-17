# -*- coding: utf-8 -*-
"""
创建个人任务 - 自动生成
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


def generate_task_code(db: Session) -> str:
    """生成任务编号：TASK-yymmdd-xxx"""
    from app.utils.number_generator import generate_sequential_no

    return generate_sequential_no(
        db=db,
        model_class=TaskUnified,
        no_field='task_code',
        prefix='TASK',
        date_format='%y%m%d',
        separator='-',
        seq_length=3
    )


def log_task_operation(
    db: Session,
    task_id: int,
    operation_type: str,
    operation_desc: str,
    operator_id: int,
    operator_name: str,
    old_value: Optional[Dict] = None,
    new_value: Optional[Dict] = None
):
    """记录任务操作日志"""
    log = TaskOperationLog(
        task_id=task_id,
        operation_type=operation_type,
        operation_desc=operation_desc,
        operator_id=operator_id,
        operator_name=operator_name,
        old_value=old_value,
        new_value=new_value
    )
    db.add(log)
    db.commit()



from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/create",
    tags=["create"]
)

# 共 1 个路由

# ==================== 创建个人任务 ====================

@router.post("/tasks", response_model=TaskUnifiedResponse, status_code=status.HTTP_201_CREATED)
def create_personal_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskUnifiedCreate,
    current_user: User = Depends(security.require_permission("task_center:create")),
) -> Any:
    """
    创建个人任务（自建任务）
    """
    # 验证项目（如果提供）
    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    task_code = generate_task_code(db)

    task = TaskUnified(
        task_code=task_code,
        title=task_in.title,
        description=task_in.description,
        task_type=task_in.task_type or "PERSONAL",
        project_id=task_in.project_id,
        assignee_id=current_user.id,
        assignee_name=current_user.real_name or current_user.username,
        assigner_id=current_user.id,
        assigner_name=current_user.real_name or current_user.username,
        plan_start_date=task_in.plan_start_date,
        plan_end_date=task_in.plan_end_date,
        deadline=task_in.deadline,
        estimated_hours=task_in.estimated_hours,
        priority=task_in.priority,
        is_urgent=task_in.is_urgent,
        tags=task_in.tags if task_in.tags else [],
        category=task_in.category,
        reminder_enabled=task_in.reminder_enabled,
        reminder_before_hours=task_in.reminder_before_hours,
        status="ACCEPTED",
        created_by=current_user.id
    )

    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if project:
            task.project_code = project.project_code
            task.project_name = project.project_name

    db.add(task)
    db.commit()
    db.refresh(task)

    log_task_operation(
        db, task.id, "CREATE", f"创建个人任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username
    )

    return get_task_detail(task.id, db, current_user)


