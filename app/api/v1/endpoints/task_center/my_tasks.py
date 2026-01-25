# -*- coding: utf-8 -*-
"""
我的任务列表 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.notification import Notification
from app.models.project import Project
from app.models.task_center import (
    JobDutyTemplate,
    TaskComment,
    TaskOperationLog,
    TaskReminder,
    TaskUnified,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.task_center import (
    BatchOperationResponse,
    BatchOperationStatistics,
    BatchTaskOperation,
    TaskCommentCreate,
    TaskCommentResponse,
    TaskOverviewResponse,
    TaskProgressUpdate,
    TaskTransferRequest,
    TaskUnifiedCreate,
    TaskUnifiedListResponse,
    TaskUnifiedResponse,
    TaskUnifiedUpdate,
)
from app.services.sales_reminder import create_notification

router = APIRouter()

# 使用统一的编码生成工具和日志工具
from .batch_helpers import generate_task_code, log_task_operation


from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/my-tasks",
    tags=["my_tasks"]
)

# 共 1 个路由

# ==================== 我的任务列表 ====================

@router.get("", response_model=TaskUnifiedListResponse, status_code=status.HTTP_200_OK)
def get_my_tasks(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    task_type: Optional[str] = Query(None, description="任务类型筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    is_urgent: Optional[bool] = Query(None, description="是否紧急"),
    is_overdue: Optional[bool] = Query(None, description="是否逾期"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索（标题/描述）"),
    sort_by: str = Query("deadline", description="排序字段：deadline/priority/created_at"),
    sort_order: str = Query("asc", description="排序方向：asc/desc"),
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    我的任务列表（聚合所有来源）
    """
    user_id = current_user.id
    query = db.query(TaskUnified).filter(TaskUnified.assignee_id == user_id)

    # 状态筛选
    if status:
        query = query.filter(TaskUnified.status == status)

    # 任务类型筛选
    if task_type:
        query = query.filter(TaskUnified.task_type == task_type)

    # 优先级筛选
    if priority:
        query = query.filter(TaskUnified.priority == priority)

    # 紧急任务筛选
    if is_urgent is not None:
        query = query.filter(TaskUnified.is_urgent == is_urgent)

    # 逾期任务筛选
    if is_overdue is not None:
        today = datetime.now().date()
        today_str = today.strftime("%Y-%m-%d")
        if is_overdue:
            query = query.filter(
                TaskUnified.deadline.isnot(None),
                func.date(TaskUnified.deadline) < today_str,
                TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"])
            )
        else:
            query = query.filter(
                or_(
                    TaskUnified.deadline.is_(None),
                    func.date(TaskUnified.deadline) >= today_str,
                    ~TaskUnified.status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS"])
                )
            )

    # 项目筛选
    if project_id:
        query = query.filter(TaskUnified.project_id == project_id)

    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                TaskUnified.title.like(f"%{keyword}%"),
                TaskUnified.description.like(f"%{keyword}%")
            )
        )

    # 排序
    if sort_by == "deadline":
        order_by = TaskUnified.deadline
    elif sort_by == "priority":
        priority_order = case(
            (TaskUnified.priority == "URGENT", 1),
            (TaskUnified.priority == "HIGH", 2),
            (TaskUnified.priority == "MEDIUM", 3),
            (TaskUnified.priority == "LOW", 4),
            else_=5
        )
        order_by = priority_order
    else:
        order_by = TaskUnified.created_at

    if sort_order == "desc":
        query = query.order_by(desc(order_by))
    else:
        query = query.order_by(order_by)

    # 总数
    total = query.count()

    # 分页
    offset = (page - 1) * page_size
    tasks = query.offset(offset).limit(page_size).all()

    # 构建响应
    items = []
    today = datetime.now().date()
    for task in tasks:
        is_overdue = False
        if task.deadline and task.status in ["PENDING", "ACCEPTED", "IN_PROGRESS"]:
            deadline_date = task.deadline.date() if isinstance(task.deadline, datetime) else task.deadline
            if deadline_date < today:
                is_overdue = True

        items.append(TaskUnifiedResponse(
            id=task.id,
            task_code=task.task_code,
            title=task.title,
            description=task.description,
            task_type=task.task_type,
            source_type=task.source_type,
            source_id=task.source_id,
            source_name=task.source_name,
            project_id=task.project_id,
            project_name=task.project_name,
            assignee_id=task.assignee_id,
            assignee_name=task.assignee_name,
            assigner_id=task.assigner_id,
            assigner_name=task.assigner_name,
            plan_start_date=task.plan_start_date,
            plan_end_date=task.plan_end_date,
            actual_start_date=task.actual_start_date,
            actual_end_date=task.actual_end_date,
            deadline=task.deadline,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours or Decimal("0"),
            status=task.status,
            progress=task.progress or 0,
            priority=task.priority,
            is_urgent=task.is_urgent or False,
            is_transferred=task.is_transferred or False,
            transfer_from_name=task.transfer_from_name,
            tags=task.tags if task.tags else [],
            category=task.category,
            is_overdue=is_overdue,
            created_at=task.created_at,
            updated_at=task.updated_at
        ))

    return TaskUnifiedListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )



