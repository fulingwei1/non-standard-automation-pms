# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 批量操作
包含：批量更新任务进度、批量分配任务负责人
"""

from typing import Any
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.progress import Task, ProgressLog
from app.schemas.progress import (
    BatchTaskProgressUpdate, BatchTaskAssigneeUpdate,
)
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== 批量操作 ====================

@router.post("/tasks/batch/progress", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: BatchTaskProgressUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量更新任务进度
    """
    if not batch_in.task_ids:
        raise HTTPException(status_code=400, detail="任务ID列表不能为空")

    if len(batch_in.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多更新50个任务")

    # 验证所有任务是否存在
    tasks = db.query(Task).filter(Task.id.in_(batch_in.task_ids)).all()
    if len(tasks) != len(batch_in.task_ids):
        raise HTTPException(status_code=404, detail="部分任务不存在")

    updated_count = 0
    updated_tasks = []

    for task in tasks:
        old_progress = task.progress_percent
        task.progress_percent = batch_in.progress_percent

        # 如果进度达到100%，自动设置为完成状态
        if batch_in.progress_percent >= 100:
            task.status = "DONE"
            if not task.actual_end:
                task.actual_end = date.today()

        # 如果进度大于0且状态为TODO，自动设置为进行中
        elif batch_in.progress_percent > 0 and task.status == "TODO":
            task.status = "IN_PROGRESS"
            if not task.actual_start:
                task.actual_start = date.today()

        db.add(task)

        # 创建进度日志
        progress_log = ProgressLog(
            task_id=task.id,
            progress_percent=batch_in.progress_percent,
            update_note=batch_in.update_note or f"批量更新进度：{old_progress}% → {batch_in.progress_percent}%",
            updated_by=current_user.id
        )
        db.add(progress_log)

        updated_tasks.append({
            "task_id": task.id,
            "task_name": task.task_name,
            "old_progress": old_progress,
            "new_progress": batch_in.progress_percent
        })
        updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"成功更新 {updated_count} 个任务进度",
        data={
            "updated_count": updated_count,
            "tasks": updated_tasks
        }
    )


@router.post("/tasks/batch/assignee", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_task_owner(
    *,
    db: Session = Depends(deps.get_db),
    batch_in: BatchTaskAssigneeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量分配任务负责人
    """
    if not batch_in.task_ids:
        raise HTTPException(status_code=400, detail="任务ID列表不能为空")

    if len(batch_in.task_ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多分配50个任务")

    # 验证负责人是否存在
    owner = db.query(User).filter(User.id == batch_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="负责人不存在")

    # 验证所有任务是否存在
    tasks = db.query(Task).filter(Task.id.in_(batch_in.task_ids)).all()
    if len(tasks) != len(batch_in.task_ids):
        raise HTTPException(status_code=404, detail="部分任务不存在")

    updated_count = 0
    updated_tasks = []

    for task in tasks:
        old_owner_id = task.owner_id
        task.owner_id = batch_in.owner_id

        db.add(task)

        # 创建进度日志
        progress_log = ProgressLog(
            task_id=task.id,
            progress_percent=task.progress_percent,
            update_note=f"批量分配负责人：{owner.real_name or owner.username}",
            updated_by=current_user.id
        )
        db.add(progress_log)

        updated_tasks.append({
            "task_id": task.id,
            "task_name": task.task_name,
            "old_owner_id": old_owner_id,
            "new_owner_id": batch_in.owner_id,
            "owner_name": owner.real_name or owner.username
        })
        updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"成功分配 {updated_count} 个任务负责人",
        data={
            "updated_count": updated_count,
            "owner_id": batch_in.owner_id,
            "owner_name": owner.real_name or owner.username,
            "tasks": updated_tasks
        }
    )
