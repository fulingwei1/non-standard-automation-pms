# -*- coding: utf-8 -*-
"""
完成任务 - 自动生成
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
    prefix="/task-center/complete",
    tags=["complete"]
)

# 共 1 个路由

# ==================== 完成任务 ====================

@router.put("/tasks/{task_id}/complete", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def complete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    完成任务
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权完成此任务")
    
    if task.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="任务已完成")
    
    old_status = task.status
    task.status = "COMPLETED"
    task.progress = 100
    task.actual_end_date = datetime.now().date()
    task.updated_by = current_user.id
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "COMPLETE", f"完成任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"status": old_status},
        new_value={"status": "COMPLETED"}
    )
    
    return get_task_detail(task_id, db, current_user)



