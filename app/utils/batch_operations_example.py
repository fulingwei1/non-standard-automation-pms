# -*- coding: utf-8 -*-
"""
批量操作框架使用示例

此文件展示了如何使用通用批量操作框架重构现有的批量操作端点。
这些示例可以直接复制到对应的端点文件中使用。
"""

from datetime import datetime
from typing import List, Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas.common import BatchOperationResponse
from app.utils.batch_operations import BatchOperationExecutor

router = APIRouter()


# ==================== 示例1: 批量完成任务 ====================

@router.post("/batch/complete", response_model=BatchOperationResponse)
def batch_complete_tasks_example(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量完成任务 - 使用框架重构后的版本
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
        from app.api.v1.endpoints.task_center.batch_helpers import log_task_operation
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


# ==================== 示例2: 批量状态更新（简化版） ====================

@router.post("/batch/start", response_model=BatchOperationResponse)
def batch_start_tasks_example(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量开始任务 - 使用框架的简化版本
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
        operation_type="BATCH_START",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


# ==================== 示例3: 使用批量状态更新方法 ====================

@router.post("/batch/pause", response_model=BatchOperationResponse)
def batch_pause_tasks_example(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量暂停任务 - 使用框架的批量状态更新方法
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.batch_status_update(
        entity_ids=task_ids,
        new_status="PAUSED",
        validator_func=lambda task: task.status == "IN_PROGRESS",
        error_message="只能暂停进行中的任务",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


# ==================== 示例4: 批量删除（软删除） ====================

@router.post("/batch/delete", response_model=BatchOperationResponse)
def batch_delete_tasks_example(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量删除任务 - 使用框架的批量删除方法
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id,
            TaskUnified.task_type == "PERSONAL"  # 只能删除个人任务
        ).all()
    
    result = executor.batch_delete(
        entity_ids=task_ids,
        validator_func=lambda task: task.task_type == "PERSONAL",
        error_message="只能删除个人任务",
        soft_delete=True,
        soft_delete_field="is_active",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())
