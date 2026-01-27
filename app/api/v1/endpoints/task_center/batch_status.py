# -*- coding: utf-8 -*-
"""
批量操作 - 状态相关操作

包含批量完成、开始、暂停、删除任务

已迁移到通用批量操作框架
"""

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas.common import BatchOperationResponse
from app.utils.batch_operations import BatchOperationExecutor

from .batch_helpers import log_task_operation

router = APIRouter()


@router.post("/batch/complete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_complete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量完成任务
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def complete_task(task: TaskUnified):
        """完成任务的操作函数"""
        task.status = "COMPLETED"
        task.progress = 100
        task.actual_end_date = datetime.now().date()
        task.updated_by = current_user.id
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        log_task_operation(
            db, task.id, "BATCH_COMPLETE", f"批量完成任务：{task.title}",
            current_user.id, current_user.real_name or current_user.username
        )
    
    # 预过滤：只处理分配给当前用户的任务
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=complete_task,
        validator_func=lambda task: task.status != "COMPLETED",
        error_message="任务已完成，不能重复完成",
        log_func=log_operation,
        operation_type="BATCH_COMPLETE",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/start", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_start_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量开始任务
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def start_task(task: TaskUnified):
        """开始任务的操作函数"""
        task.status = "IN_PROGRESS"
        if not task.actual_start_date:
            task.actual_start_date = datetime.now().date()
        task.updated_by = current_user.id
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        old_status = getattr(task, '_old_status', task.status)
        log_task_operation(
            db, task.id, "BATCH_START", f"批量开始任务：{task.title}",
            current_user.id, current_user.real_name or current_user.username,
            old_value={"status": old_status},
            new_value={"status": "IN_PROGRESS"}
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=start_task,
        validator_func=lambda task: task.status not in ["IN_PROGRESS", "COMPLETED"],
        error_message="任务已开始或已完成",
        log_func=log_operation,
        operation_type="BATCH_START",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/pause", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_pause_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量暂停任务
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def pause_task(task: TaskUnified):
        """暂停任务的操作函数"""
        task.status = "PAUSED"
        task.updated_by = current_user.id
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        old_status = getattr(task, '_old_status', task.status)
        log_task_operation(
            db, task.id, "BATCH_PAUSE", f"批量暂停任务：{task.title}",
            current_user.id, current_user.real_name or current_user.username,
            old_value={"status": old_status},
            new_value={"status": "PAUSED"}
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=pause_task,
        validator_func=lambda task: task.status == "IN_PROGRESS",
        error_message="只能暂停进行中的任务",
        log_func=log_operation,
        operation_type="BATCH_PAUSE",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/delete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_delete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量删除任务（仅个人任务，硬删除）
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def delete_task(task: TaskUnified):
        """删除任务的操作函数（硬删除）"""
        db.delete(task)
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志（在删除前记录）"""
        log_task_operation(
            db, task.id, "BATCH_DELETE", f"批量删除任务：{task.title}",
            current_user.id, current_user.real_name or current_user.username
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id,
            TaskUnified.task_type == "PERSONAL"  # 只能删除个人任务
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=delete_task,
        validator_func=lambda task: task.task_type == "PERSONAL",
        error_message="只能删除个人任务",
        log_func=log_operation,
        operation_type="BATCH_DELETE",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())
