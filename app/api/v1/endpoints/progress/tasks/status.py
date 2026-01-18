# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务状态管理
包含：任务完成、阻塞、解除阻塞、取消
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.progress import ProgressLog, Task
from app.models.user import User
from app.schemas.progress import TaskResponse

router = APIRouter()


@router.put("/tasks/{task_id}/complete", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def complete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "DONE"
    task.progress_percent = 100
    if not task.actual_end:
        task.actual_end = date.today()
    if not task.actual_start:
        task.actual_start = task.plan_start or date.today()

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=100,
        update_note="任务完成",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/block", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def block_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    block_reason: str = Query(..., description="阻塞原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    阻塞任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    task.status = "BLOCKED"
    task.block_reason = block_reason

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=task.progress_percent,
        update_note=f"任务阻塞：{block_reason}",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/unblock", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def unblock_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    解除任务阻塞
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status != "BLOCKED":
        raise HTTPException(status_code=400, detail="任务当前不是阻塞状态")

    # 根据进度恢复状态
    if task.progress_percent >= 100:
        task.status = "DONE"
    elif task.progress_percent > 0:
        task.status = "IN_PROGRESS"
    else:
        task.status = "TODO"

    task.block_reason = None

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=task.progress_percent,
        update_note="任务解除阻塞",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.put("/tasks/{task_id}/cancel", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def cancel_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    cancel_reason: Optional[str] = Query(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    if task.status == "DONE":
        raise HTTPException(status_code=400, detail="已完成的任务不能取消")

    task.status = "CANCELLED"
    if cancel_reason:
        task.block_reason = cancel_reason

    # 创建进度日志
    progress_log = ProgressLog(
        task_id=task_id,
        progress_percent=task.progress_percent,
        update_note=f"任务取消：{cancel_reason or '无原因'}",
        updated_by=current_user.id
    )
    db.add(progress_log)

    db.add(task)
    db.commit()
    db.refresh(task)

    return task
