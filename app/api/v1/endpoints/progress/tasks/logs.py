# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务进度日志
包含：任务进度日志查询
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.progress import ProgressLog, Task
from app.models.user import User
from app.schemas.progress import ProgressLogListResponse, ProgressLogResponse

router = APIRouter()


@router.get("/tasks/{task_id}/logs", response_model=ProgressLogListResponse, status_code=status.HTTP_200_OK)
def get_task_progress_logs(
    task_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务进度日志
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    query = db.query(ProgressLog).filter(ProgressLog.task_id == task_id)

    total = query.count()
    offset = (page - 1) * page_size
    logs = query.order_by(ProgressLog.updated_at.desc()).offset(offset).limit(page_size).all()

    # 补充更新人姓名
    items = []
    for log in logs:
        updater_name = None
        if log.updated_by:
            updater = db.query(User).filter(User.id == log.updated_by).first()
            updater_name = updater.real_name or updater.username if updater else None

        items.append(ProgressLogResponse(
            id=log.id,
            task_id=log.task_id,
            progress_percent=log.progress_percent,
            update_note=log.update_note,
            updated_by=log.updated_by,
            updated_by_name=updater_name,
            updated_at=log.updated_at
        ))

    return ProgressLogListResponse(
        items=items,
        total=total
    )
