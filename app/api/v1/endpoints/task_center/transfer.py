# -*- coding: utf-8 -*-
"""
任务转办 - 自动生成
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
    prefix="/task-center/transfer",
    tags=["transfer"]
)

# 共 1 个路由

# ==================== 任务转办 ====================

@router.post("/tasks/{task_id}/transfer", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def transfer_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    transfer_in: TaskTransferRequest,
    current_user: User = Depends(security.require_permission("task_center:assign")),
) -> Any:
    """
    任务转办
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权转办此任务")
    
    if task.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="已完成的任务不能转办")
    
    # 验证目标用户
    target_user = db.query(User).filter(User.id == transfer_in.target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")
    
    if target_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能转办给自己")
    
    old_assignee_id = task.assignee_id
    old_assignee_name = task.assignee_name
    
    task.assignee_id = transfer_in.target_user_id
    task.assignee_name = target_user.real_name or target_user.username
    task.is_transferred = True
    task.transfer_from_id = current_user.id
    task.transfer_from_name = current_user.real_name or current_user.username
    task.transfer_reason = transfer_in.transfer_reason
    task.transfer_time = datetime.now()
    task.status = "PENDING"  # 转办后需要接收
    task.updated_by = current_user.id
    
    db.add(task)
    db.commit()
    db.refresh(task)
    
    log_task_operation(
        db, task.id, "TRANSFER",
        f"转办任务：{old_assignee_name} -> {task.assignee_name}，原因：{transfer_in.transfer_reason}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"assignee_id": old_assignee_id, "assignee_name": old_assignee_name},
        new_value={"assignee_id": transfer_in.target_user_id, "assignee_name": task.assignee_name}
    )
    
    # 发送通知给目标用户
    try:
        target_user = db.query(User).filter(User.id == transfer_in.target_user_id).first()
        if target_user:
            notification = create_notification(
                db=db,
                user_id=transfer_in.target_user_id,
                notification_type="TASK_ASSIGNED",
                title=f"任务转办通知",
                content=f"{current_user.real_name or current_user.username} 将任务「{task.title}」转办给您，原因：{transfer_in.transfer_reason}",
                source_type="task",
                source_id=task.id,
                link_url=f"/tasks/{task.id}",
                priority="HIGH",
                extra_data={"task_id": task.id, "from_user": current_user.real_name or current_user.username}
            )
            db.commit()
    except Exception as e:
        # 通知发送失败不影响主流程
        pass
    
    return get_task_detail(task_id, db, current_user)



