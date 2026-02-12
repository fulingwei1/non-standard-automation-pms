# -*- coding: utf-8 -*-
"""
工程师任务管理 API 端点
包含：任务创建、列表查询、任务详情
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.project import Project, ProjectMember
from app.models.task_center import (
    TaskApprovalWorkflow,
    TaskCompletionProof,
    TaskUnified,
)
from app.models.user import User
from app.schemas import engineer as schemas
from app.common.query_filters import apply_pagination

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tasks", response_model=schemas.TaskResponse)
def create_task(
    task_data: schemas.TaskCreateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:create"))
):
    """
    创建任务（支持智能审批路由）
    - IMPORTANT 任务：需要PM审批
    - GENERAL 任务：直接创建
    """
    # 验证项目存在且用户是成员
    project = db.query(Project).filter(Project.id == task_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查用户是否是项目成员
    is_member = db.query(ProjectMember).filter(
        and_(
            ProjectMember.project_id == task_data.project_id,
            ProjectMember.user_id == current_user.id,
            ProjectMember.is_active
        )
    ).first()

    if not is_member:
        raise HTTPException(status_code=403, detail="您不是该项目的成员")

    # 验证IMPORTANT任务必须填写justification
    if task_data.task_importance == 'IMPORTANT' and not task_data.justification:
        raise HTTPException(status_code=400, detail="重要任务必须说明必要性")

    # 生成任务编号
    task_code = f"TASK-{datetime.now().strftime('%y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # 确定初始状态
    if task_data.task_importance == 'IMPORTANT':
        initial_status = 'PENDING_APPROVAL'
        approval_required = True
        approval_status = 'PENDING_APPROVAL'
    else:
        initial_status = 'ACCEPTED'
        approval_required = False
        approval_status = None

    # 创建任务
    new_task = TaskUnified(
        task_code=task_code,
        title=task_data.title,
        description=task_data.description,
        task_type='PROJECT_WBS',
        source_type='MANUAL',

        project_id=task_data.project_id,
        project_code=project.project_code,
        project_name=project.project_name,
        wbs_code=task_data.wbs_code,

        assignee_id=current_user.id,
        assignee_name=current_user.real_name,
        assigner_id=current_user.id,
        assigner_name=current_user.real_name,

        plan_start_date=task_data.plan_start_date,
        plan_end_date=task_data.plan_end_date,
        deadline=task_data.deadline,

        estimated_hours=task_data.estimated_hours,
        actual_hours=0,

        status=initial_status,
        progress=0,
        priority=task_data.priority,

        approval_required=approval_required,
        approval_status=approval_status,
        task_importance=task_data.task_importance,

        tags=task_data.tags,
        category=task_data.category,

        created_by=current_user.id,
        updated_by=current_user.id
    )

    db.add(new_task)
    db.flush()

    # 如果是IMPORTANT任务，创建审批工作流
    if task_data.task_importance == 'IMPORTANT':
        approval_workflow = TaskApprovalWorkflow(
            task_id=new_task.id,
            submitted_by=current_user.id,
            submitted_at=datetime.now(),
            submit_note=task_data.justification,
            approver_id=project.pm_id,  # 项目经理
            approval_status='PENDING',
            task_details={
                'title': task_data.title,
                'description': task_data.description,
                'estimated_hours': float(task_data.estimated_hours) if task_data.estimated_hours else None
            }
        )
        db.add(approval_workflow)

        # 发送通知给PM
        from app.services.notification_dispatcher import NotificationDispatcher
        from app.services.channel_handlers.base import NotificationRequest, NotificationPriority
        try:
            dispatcher = NotificationDispatcher(db)
            request = NotificationRequest(
                recipient_id=project.pm_id,
                notification_type="TASK_ASSIGNED",
                category="task",
                title=f"待审批：{task_data.title}",
                content=f"提交人：{current_user.real_name or current_user.username}\n说明：{task_data.justification or '无'}",
                priority=NotificationPriority.NORMAL,
                source_type="task",
                source_id=new_task.id,
                link_url=f"/engineers/tasks/{new_task.id}",
            )
            dispatcher.send_notification_request(request)
        except Exception:
            # 通知失败不影响主流程
            logger.warning("任务创建审批通知发送失败，不影响主流程", exc_info=True)

    db.commit()
    db.refresh(new_task)

    # 构建响应
    response = schemas.TaskResponse.model_validate(new_task)
    response.proof_count = 0  # 新任务没有证明

    return response


@router.get("/tasks", response_model=schemas.TaskListResponse)
def get_my_tasks(
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = None,
    task_status: Optional[str] = None,
    priority: Optional[str] = None,
    is_delayed: Optional[bool] = None,
    is_overdue: Optional[bool] = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取我的任务列表（支持多种筛选条件）
    """
    # 构建查询
    query = db.query(TaskUnified).filter(
        TaskUnified.assignee_id == current_user.id
    )

    # 应用筛选条件
    if project_id:
        query = query.filter(TaskUnified.project_id == project_id)

    if task_status:
        query = query.filter(TaskUnified.status == task_status)

    if priority:
        query = query.filter(TaskUnified.priority == priority)

    if is_delayed is not None:
        query = query.filter(TaskUnified.is_delayed == is_delayed)

    if is_overdue is not None:
        # 逾期任务：截止时间<当前时间 且 状态不是已完成/已取消
        if is_overdue:
            query = query.filter(
                and_(
                    TaskUnified.deadline < datetime.now(),
                    TaskUnified.status.notin_(['COMPLETED', 'CANCELLED'])
                )
            )
        else:
            # 未逾期任务
            query = query.filter(
                or_(
                    TaskUnified.deadline >= datetime.now(),
                    TaskUnified.deadline.is_(None),
                    TaskUnified.status.in_(['COMPLETED', 'CANCELLED'])
                )
            )

    # 排序：优先级+截止时间
    query = query.order_by(
        TaskUnified.priority.desc(),
        TaskUnified.deadline.asc()
    )

    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        total = 0
    tasks = apply_pagination(query, pagination.offset, pagination.limit).all()

    # 构建响应
    items = []
    for task in tasks:
        proof_count = db.query(TaskCompletionProof).filter(
            TaskCompletionProof.task_id == task.id
        ).count()

        task_response = schemas.TaskResponse.model_validate(task)
        task_response.proof_count = proof_count
        items.append(task_response)

    total = int(total) if total is not None else 0

    return schemas.TaskListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/tasks/{task_id}", response_model=schemas.TaskResponse)
def get_task_detail(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取任务详情
    """
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限（任务相关人员可查看）
    if task.assignee_id != current_user.id and task.created_by != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project or project.pm_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看此任务")

    # 获取证明数量
    proof_count = db.query(TaskCompletionProof).filter(
        TaskCompletionProof.task_id == task_id
    ).count()

    task_response = schemas.TaskResponse.model_validate(task)
    task_response.proof_count = proof_count

    return task_response
