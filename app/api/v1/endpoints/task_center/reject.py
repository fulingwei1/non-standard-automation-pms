# -*- coding: utf-8 -*-
"""
接收/拒绝转办任务 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.services.sales_reminder import create_notification
from app.utils.db_helpers import get_or_404

from .detail import get_task_detail

router = APIRouter()
logger = logging.getLogger(__name__)

# 使用统一的编码生成工具和日志工具
from .batch_helpers import log_task_operation


from fastapi import APIRouter

router = APIRouter(
    prefix="/reject",
    tags=["reject"]
)

# 共 2 个路由

# ==================== 接收/拒绝转办任务 ====================

@router.put("/tasks/{task_id}/accept", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def accept_transferred_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    接收转办任务
    """
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权接收此任务")

    if task.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能接收待接收状态的任务")

    old_status = task.status
    task.status = "ACCEPTED"
    task.updated_by = current_user.id

    db.add(task)
    db.commit()
    db.refresh(task)

    log_task_operation(
        db, task.id, "ACCEPT", f"接收转办任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username,
        old_value={"status": old_status},
        new_value={"status": "ACCEPTED"}
    )

    return get_task_detail(task_id, db, current_user)


@router.put("/tasks/{task_id}/reject", response_model=TaskUnifiedResponse, status_code=status.HTTP_200_OK)
def reject_transferred_task(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    reason: Optional[str] = Query(None, description="拒绝原因"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    拒绝转办任务
    """
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    if task.assignee_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权拒绝此任务")

    if task.status != "PENDING":
        raise HTTPException(status_code=400, detail="只能拒绝待接收状态的任务")

    # 拒绝后转回给原转办人
    if task.transfer_from_id:
        old_assignee_id = task.assignee_id
        old_assignee_name = task.assignee_name

        from_user = db.query(User).filter(User.id == task.transfer_from_id).first()
        if from_user:
            task.assignee_id = task.transfer_from_id
            task.assignee_name = from_user.real_name or from_user.username
            task.is_transferred = False
            task.status = "ACCEPTED"
            task.updated_by = current_user.id

            db.add(task)
            db.commit()
            db.refresh(task)

            log_task_operation(
                db, task.id, "REJECT",
                f"拒绝转办任务，原因：{reason or '未提供原因'}",
                current_user.id, current_user.real_name or current_user.username,
                old_value={"assignee_id": old_assignee_id, "assignee_name": old_assignee_name},
                new_value={"assignee_id": task.transfer_from_id, "assignee_name": task.assignee_name}
            )

            # 通知原转办人
            if task.transfer_from_id:
                try:
                    create_notification(
                        db=db,
                        user_id=task.transfer_from_id,
                        notification_type="TASK_TRANSFER_REJECTED",
                        title="任务转办被拒绝",
                        content=f"{current_user.real_name or current_user.username} 拒绝了任务「{task.title}」的转办，原因：{reason or '未提供原因'}",
                        source_type="task",
                        source_id=task.id,
                        link_url=f"/tasks/{task.id}",
                        priority="NORMAL",
                        extra_data={"task_id": task.id, "reject_reason": reason}
                    )
                    db.commit()
                except Exception:
                    # 通知发送失败不影响主流程
                    logger.warning("任务转办拒绝通知发送失败，不影响主流程", exc_info=True)

    return get_task_detail(task_id, db, current_user)
