# -*- coding: utf-8 -*-
"""
更新任务进度 - 使用统一 TaskProgressService
从 task_center.py 拆分，与 engineers/progress 共用进度更新逻辑
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.task_center import TaskProgressUpdate, TaskUnifiedResponse
from app.services.task_progress_service import update_task_progress as update_task_progress_service

from .detail import get_task_detail
from .batch_helpers import log_task_operation

router = APIRouter(
    prefix="/task-center/update",
    tags=["update"],
)


def _progress_error_to_http(exc: ValueError) -> HTTPException:
    """将服务层 ValueError 映射为 HTTP 异常"""
    msg = str(exc)
    if "任务不存在" in msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    if "只能更新" in msg or "无权" in msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.put("/tasks/{task_id}/progress", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def update_task_progress(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    progress_in: TaskProgressUpdate,
    current_user: User = Depends(security.require_permission("task_center:update")),
) -> Any:
    """
    更新任务进度（与工程师进度接口共用 TaskProgressService）
    """
    try:
        task, _ = update_task_progress_service(
            db,
            task_id=task_id,
            progress=progress_in.progress,
            updater_id=current_user.id,
            actual_hours=progress_in.actual_hours,
            progress_note=progress_in.note,
            reject_completed=False,
            create_progress_log=bool(progress_in.note),
            run_aggregation=True,
        )
    except ValueError as e:
        raise _progress_error_to_http(e)

    log_task_operation(
        db,
        task.id,
        "UPDATE_PROGRESS",
        f"更新进度：{task.progress}%",
        current_user.id,
        current_user.real_name or current_user.username,
        old_value={},
        new_value={
            "progress": task.progress,
            "actual_hours": float(task.actual_hours) if task.actual_hours else None,
        },
    )

    return get_task_detail(db=db, task_id=task_id, current_user=current_user)


