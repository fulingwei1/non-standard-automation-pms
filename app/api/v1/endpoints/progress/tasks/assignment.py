# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 任务分配
包含：任务负责人分配
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.progress import Task
from app.models.user import User
from app.schemas.progress import TaskAssigneeUpdate, TaskResponse

router = APIRouter()


@router.put("/tasks/{task_id}/assignee", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def assign_task_owner(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    assignee_in: TaskAssigneeUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    分配任务负责人
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证用户是否存在
    owner = db.query(User).filter(User.id == assignee_in.owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="用户不存在")

    task.owner_id = assignee_in.owner_id
    db.add(task)
    db.commit()
    db.refresh(task)

    return task
