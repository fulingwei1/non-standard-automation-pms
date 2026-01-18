# -*- coding: utf-8 -*-
"""
批量操作 - 状态相关操作

包含批量完成、开始、暂停、删除任务
"""

from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.task_center import TaskUnified
from app.models.user import User
from app.schemas.task_center import BatchOperationResponse

from .batch_helpers import log_task_operation

router = APIRouter()


@router.post("/batch/complete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_complete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量完成任务
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
                failed_tasks.append({"task_id": task.id, "reason": "任务已完成"})
                continue

            task.status = "COMPLETED"
            task.progress = 100
            task.actual_end_date = datetime.now().date()
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_COMPLETE", f"批量完成任务：{task.title}",
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


@router.post("/batch/start", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_start_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量开始任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status in ["IN_PROGRESS", "COMPLETED"]:
                failed_tasks.append({"task_id": task.id, "reason": "任务已开始或已完成"})
                continue

            old_status = task.status
            task.status = "IN_PROGRESS"
            if not task.actual_start_date:
                task.actual_start_date = datetime.now().date()
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_START", f"批量开始任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"status": old_status},
                new_value={"status": "IN_PROGRESS"}
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


@router.post("/batch/pause", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_pause_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量暂停任务
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.status != "IN_PROGRESS":
                failed_tasks.append({"task_id": task.id, "reason": "只能暂停进行中的任务"})
                continue

            old_status = task.status
            task.status = "PAUSED"
            task.updated_by = current_user.id

            log_task_operation(
                db, task.id, "BATCH_PAUSE", f"批量暂停任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"status": old_status},
                new_value={"status": "PAUSED"}
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


@router.post("/batch/delete", response_model=BatchOperationResponse, status_code=status.HTTP_200_OK)
def batch_delete_tasks(
    *,
    db: Session = Depends(deps.get_db),
    task_ids: List[int] = Body(..., description="任务ID列表"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    批量删除任务（仅个人任务）
    """
    tasks = db.query(TaskUnified).filter(
        TaskUnified.id.in_(task_ids),
        TaskUnified.assignee_id == current_user.id,
        TaskUnified.task_type == "PERSONAL"  # 只能删除个人任务
    ).all()

    success_count = 0
    failed_tasks = []

    for task in tasks:
        try:
            if task.task_type != "PERSONAL":
                failed_tasks.append({"task_id": task.id, "reason": "只能删除个人任务"})
                continue

            log_task_operation(
                db, task.id, "BATCH_DELETE", f"批量删除任务：{task.title}",
                current_user.id, current_user.real_name or current_user.username
            )

            db.delete(task)
            success_count += 1
        except Exception as e:
            failed_tasks.append({"task_id": task.id, "reason": str(e)})

    db.commit()

    return BatchOperationResponse(
        success_count=success_count,
        failed_count=len(failed_tasks),
        failed_tasks=failed_tasks
    )
