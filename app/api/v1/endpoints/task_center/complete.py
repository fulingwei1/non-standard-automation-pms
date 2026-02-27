# -*- coding: utf-8 -*-
"""
完成任务 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.task_center import (
    TaskUnified,
)
from app.models.user import User
from app.schemas.task_center import (
    TaskUnifiedResponse,
)
from app.utils.db_helpers import get_or_404

from .detail import get_task_detail

router = APIRouter()

# 使用统一的编码生成工具和日志工具
from .batch_helpers import log_task_operation

router = APIRouter(
    prefix="",
    tags=["complete"]
)

# 共 1 个路由

# ==================== 完成任务 ====================

@router.put("/tasks/{task_id}/complete", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def complete_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    完成任务
    """
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权完成此任务")

    if task.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="任务已完成")

    old_status = task.status
    task.status = "COMPLETED"
    task.progress = 100
    task.actual_end_date = datetime.now().date()
    task.updated_by = current_user.id

    db.add(task)
    db.commit()
    db.refresh(task)

    log_task_operation(
        db, task.id, "COMPLETE", f"完成任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"status": old_status},
        new_value={"status": "COMPLETED"}
    )

    return get_task_detail(task_id, db, current_user)


