# -*- coding: utf-8 -*-
"""
批量操作 - 属性相关操作

包含批量转办、设置优先级、更新进度、标签、催办

已迁移到通用批量操作框架
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.notification import Notification
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas.common import BatchOperationResponse
from app.utils.batch_operations import BatchOperationExecutor, BatchOperationResult

from .batch_helpers import log_task_operation

router = APIRouter()


@router.post("/batch/transfer", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_transfer_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    target_user_id: int = Body(..., description="目标用户ID"),
    transfer_reason: str = Body(..., description="转办原因"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量转办任务
    """
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def transfer_task(task: TaskUnified):
        """转办任务的操作函数"""
        task.assignee_id = target_user_id
        task.assignee_name = target_user.real_name or target_user.username
        task.is_transferred = True
        task.transfer_from_id = current_user.id
        task.transfer_from_name = current_user.real_name or current_user.username
        task.transfer_reason = transfer_reason
        task.transfer_time = datetime.now()
        task.status = "PENDING"
        task.updated_by = current_user.id
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        log_task_operation(
            db, task.id, "BATCH_TRANSFER",
            f"批量转办任务：{task.title} -> {target_user.real_name or target_user.username}",
            current_user.id, current_user.real_name or current_user.username
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=transfer_task,
        validator_func=lambda task: task.status != "COMPLETED",
        error_message="已完成的任务不能转办",
        log_func=log_operation,
        operation_type="BATCH_TRANSFER",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/priority", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_set_priority(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    priority: str = Body(..., description="优先级（LOW/MEDIUM/HIGH/URGENT）"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量设置优先级
    """
    if priority not in ["URGENT", "HIGH", "MEDIUM", "LOW"]:
        raise HTTPException(status_code=400, detail="无效的优先级")

    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def set_priority(task: TaskUnified):
        """设置优先级的操作函数"""
        task.priority = priority
        task.updated_by = current_user.id
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        old_priority = getattr(task, '_old_priority', task.priority)
        log_task_operation(
            db, task.id, "BATCH_SET_PRIORITY",
            f"批量设置优先级：{old_priority} -> {priority}",
            current_user.id, current_user.real_name or current_user.username,
            old_value={"priority": old_priority},
            new_value={"priority": priority}
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=set_priority,
        log_func=log_operation,
        operation_type="BATCH_SET_PRIORITY",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/progress", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_update_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    progress: int = Body(..., ge=0, le=100, description="进度百分比（0-100）"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量更新进度
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def update_progress(task: TaskUnified):
        """更新进度的操作函数"""
        task.progress = progress
        task.updated_by = current_user.id
        
        if progress >= 100 and task.status != "COMPLETED":
            task.status = "COMPLETED"
            task.actual_end_date = datetime.now().date()
        
        if progress > 0 and task.status == "ACCEPTED":
            task.status = "IN_PROGRESS"
            if not task.actual_start_date:
                task.actual_start_date = datetime.now().date()
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        old_progress = getattr(task, '_old_progress', task.progress)
        log_task_operation(
            db, task.id, "BATCH_UPDATE_PROGRESS",
            f"批量更新进度：{old_progress}% -> {progress}%",
            current_user.id, current_user.real_name or current_user.username,
            old_value={"progress": old_progress},
            new_value={"progress": progress}
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=update_progress,
        validator_func=lambda task: task.status != "COMPLETED",
        error_message="已完成的任务不能更新进度",
        log_func=log_operation,
        operation_type="BATCH_UPDATE_PROGRESS",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/tag", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_tag_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    tags: List[str] = Body(..., description="标签列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量添加标签
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def add_tags(task: TaskUnified):
        """添加标签的操作函数"""
        existing_tags = task.tags or []
        # 合并标签，去重
        new_tags = list(set(existing_tags + tags))
        task.tags = new_tags
        task.updated_by = current_user.id
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        old_tags = getattr(task, '_old_tags', task.tags)
        new_tags = task.tags
        log_task_operation(
            db, task.id, "BATCH_TAG",
            f"批量添加标签：{task.title} -> {', '.join(tags)}",
            current_user.id, current_user.real_name or current_user.username,
            old_value={"tags": old_tags},
            new_value={"tags": new_tags}
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids),
            TaskUnified.assignee_id == current_user.id
        ).all()
    
    result = executor.execute(
        entity_ids=task_ids,
        operation_func=add_tags,
        log_func=log_operation,
        operation_type="BATCH_TAG",
        pre_filter_func=pre_filter
    )
    
    return BatchOperationResponse(**result.to_dict())


@router.post("/batch/urge", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_urge_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    urge_message: Optional[str] = Body(None, description="催办消息"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> BatchOperationResponse:
    """
    批量催办任务（发送催办通知）
    """
    executor = BatchOperationExecutor(
        model=TaskUnified,
        db=db,
        current_user=current_user
    )
    
    def urge_task(task: TaskUnified):
        """催办任务的操作函数"""
        # 创建催办通知
        notification = Notification(
            user_id=task.assignee_id,
            notification_type="TASK_URGE",
            title=f"任务催办：{task.title}",
            content=urge_message or f"任务【{task.title}】需要尽快处理，请及时关注。",
            source_type="TASK",
            source_id=task.id,
            link_url=f"/task-center/tasks/{task.id}",
            priority="HIGH",
            extra_data={
                "task_id": task.id,
                "task_title": task.title,
                "urge_by": current_user.real_name or current_user.username,
                "urge_by_id": current_user.id
            }
        )
        db.add(notification)
    
    def log_operation(task: TaskUnified, op_type: str):
        """记录操作日志"""
        log_task_operation(
            db, task.id, "BATCH_URGE",
            f"批量催办任务：{task.title}",
            current_user.id, current_user.real_name or current_user.username
        )
    
    def pre_filter(db: Session, ids: List[int]) -> List[TaskUnified]:
        return db.query(TaskUnified).filter(
            TaskUnified.id.in_(ids)
        ).all()
    
    def validate_urge(task: TaskUnified) -> bool:
        """验证是否可以催办"""
        if not task.assignee_id:
            return False
        if task.status == "COMPLETED":
            return False
        return True
    
    # 使用自定义验证逻辑，因为错误消息需要根据任务状态动态生成
    result = BatchOperationResult()
    tasks = pre_filter(db, task_ids)
    task_map = {task.id: task for task in tasks}
    
    for task_id in task_ids:
        task = task_map.get(task_id)
        if not task:
            result.add_failure(task_id, "任务不存在或无访问权限", id_field="task_id")
            continue
        
        try:
            if not validate_urge(task):
                # 根据任务状态生成错误消息
                if not task.assignee_id:
                    error_msg = "任务未分配负责人"
                elif task.status == "COMPLETED":
                    error_msg = "已完成的任务无需催办"
                else:
                    error_msg = "无法催办"
                result.add_failure(task_id, error_msg, id_field="task_id")
                continue
            
            urge_task(task)
            log_operation(task, "BATCH_URGE")
            db.add(task)  # 确保任务也被添加到会话
            result.add_success()
        except Exception as e:
            result.add_failure(task_id, str(e), id_field="task_id")
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        # 如果提交失败，记录错误
        for item in result.failed_items:
            if item.get("task_id") not in [t.id for t in tasks]:
                result.add_failure(item.get("task_id", 0), f"事务提交失败: {str(e)}", id_field="task_id")
    
    return BatchOperationResponse(**result.to_dict(id_field="task_id"))
