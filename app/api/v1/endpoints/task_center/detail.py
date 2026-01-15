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

from typing import Any, List, Optional, Dict
from datetime import date, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_, func, case

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project
from app.models.notification import Notification
from app.services.sales_reminder_service import create_notification
from app.models.task_center import (
    TaskUnified, TaskComment, TaskOperationLog, TaskReminder, JobDutyTemplate
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.schemas.task_center import (
    TaskOverviewResponse, TaskUnifiedCreate, TaskUnifiedUpdate, TaskUnifiedResponse,
    TaskUnifiedListResponse, TaskProgressUpdate, TaskTransferRequest,
    TaskCommentCreate, TaskCommentResponse, BatchTaskOperation, BatchOperationResponse,
    BatchOperationStatistics
)

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



