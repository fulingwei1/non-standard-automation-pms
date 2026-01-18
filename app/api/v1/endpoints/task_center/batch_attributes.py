# -*- coding: utf-8 -*-
"""
批量操作 - 属性相关操作

包含批量转办、设置优先级、更新进度、标签、催办
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
from app.schemas.task_center import BatchOperationResponse

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
) -> Any:
    """
    批量转办任务
    """
    target_user = db.query(User).filter(User.id == target_user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="目标用户不存在")

    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务不能转办"})
                continue

            task.assignee_id = target_user_id
            task.assignee_name = target_user.real_name or target_user.username
            task.is_transferred = True
            task.transfer_from_id = current_user.id
            task.transfer_from_name = current_user.real_name or current_user.username
            task.transfer_reason = transfer_reason
            task.transfer_time = datetime.now()
            task.status = "PENDING"
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_TRANSFER",
                f"批量转办任务：{task.title} -> {target_user.real_name or target_user.username}",
                current_user.id, current_user.real_name or current_user.username
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/priority", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_set_priority(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    priority: str = Body(..., description="优先级（LOW/MEDIUM/HIGH/URGENT）"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量设置优先级
    """
    if priority not in ["URGENT", "HIGH", "MEDIUM", "LOW"]:
        raise HTTPException(status_code=400, detail="无效的优先级")

    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            old_priority = task.priority
            task.priority = priority
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_SET_PRIORITY",
                f"批量设置优先级：{old_priority} -> {priority}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"priority": old_priority},
                new_value={"priority": priority}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/progress", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_update_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    progress: int = Body(..., ge=0, le=100, description="进度百分比（0-100）"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量更新进度
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务不能更新进度"})
                continue

            old_progress = task.progress
            task.progress = progress
            task.updated_by = current_user.id

            if progress >= 100 and task.status != "COMPLETED":
                task.status = "COMPLETED"
                task.actual_end_date = datetime.now().date()

            if progress > 0 and task.status == "ACCEPTED":
                task.status = "IN_PROGRESS"
                if not task.actual_start_date:
                    task.actual_start_date = datetime.now().date()

            log_task_operation(
                db, task.id, "BATCH_UPDATE_PROGRESS",
                f"批量更新进度：{old_progress}% -> {progress}%",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"progress": old_progress},
                new_value={"progress": progress}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/tag", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_tag_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    tags: List[str] = Body(..., description="标签列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量添加标签
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            existing_tags = task.tags or []
            # 合并标签，去重
            new_tags = list(set(existing_tags + tags))
            old_tags = task.tags
            task.tags = new_tags
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_TAG",
                f"批量添加标签：{task.title} -> {', '.join(tags)}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"tags": old_tags},
                new_value={"tags": new_tags}
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )


@router.post("/batch/urge", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_urge_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    urge_message: Optional[str] = Body(None, description="催办消息"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量催办任务（发送催办通知）
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids)
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if not task.assignee_id:
                failed_tasks.append({"task_id": task.id, "reason": "任务未分配负责人"})
                continue

            if task.status == "COMPLETED":
                failed_tasks.append({"task_id": task.id, "reason": "已完成的任务无需催办"})
                continue

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

            log_task_operation(
                db, task.id, "BATCH_URGE",
                f"批量催办任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )

            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )
