# -*- coding: utf-8 -*-
"""
创建个人任务 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.task_center import (
    TaskUnified,
)
from app.models.user import User
from app.schemas.task_center import (
    TaskUnifiedCreate,
    TaskUnifiedResponse,
)

from .detail import get_task_detail

router = APIRouter()

# 使用统一的编码生成工具和日志工具
from .batch_helpers import generate_task_code, log_task_operation


from fastapi import APIRouter

router = APIRouter(
    prefix="",
    tags=["create"]
)

# 共 1 个路由

# ==================== 创建个人任务 ====================

@router.post("/tasks", response_model=TaskUnifiedResponse, status_code=status.HTTP_201_CREATED)
def create_personal_task(
    *,
    db: Session = Depends(deps.get_db),
    task_in: TaskUnifiedCreate,
    current_user: User = Depends(security.require_permission("task_center:create")),
) -> Any:
    """
    创建个人任务（自建任务）
    """
    # 验证项目（如果提供）
    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    task_code = generate_task_code(db)

    task = TaskUnified(
        task_code=task_code,
        title=task_in.title,
        description=task_in.description,
        task_type=task_in.task_type or "PERSONAL",
        project_id=task_in.project_id,
        assignee_id=current_user.id,
        assignee_name=current_user.real_name or current_user.username,
        assigner_id=current_user.id,
        assigner_name=current_user.real_name or current_user.username,
        plan_start_date=task_in.plan_start_date,
        plan_end_date=task_in.plan_end_date,
        deadline=task_in.deadline,
        estimated_hours=task_in.estimated_hours,
        priority=task_in.priority,
        is_urgent=task_in.is_urgent,
        tags=task_in.tags if task_in.tags else [],
        category=task_in.category,
        reminder_enabled=task_in.reminder_enabled,
        reminder_before_hours=task_in.reminder_before_hours,
        status="ACCEPTED",
        created_by=current_user.id
    )

    if task_in.project_id:
        project = db.query(Project).filter(Project.id == task_in.project_id).first()
        if project:
            task.project_code = project.project_code
            task.project_name = project.project_name

    db.add(task)
    db.commit()
    db.refresh(task)

    log_task_operation(
        db, task.id, "CREATE", f"创建个人任务：{task.title}",
        current_user.id, current_user.real_name or current_user.username
    )

    return get_task_detail(task.id, db, current_user)


