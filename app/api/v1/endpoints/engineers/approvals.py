# -*- coding: utf-8 -*-
"""
工程师任务审批 API 端点
包含：PM审批任务、审批历史查询
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.task_center import (
    TaskApprovalWorkflow,
    TaskCompletionProof,
    TaskUnified,
)
from app.models.user import User
from app.schemas import engineer as schemas

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/tasks/pending-approval", response_model=schemas.TaskListResponse)
def get_pending_approval_tasks(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取待我审批的任务列表（PM视图）
    """
    # 查询当前用户作为PM的项目
    pm_projects = db.query(Project).filter(Project.pm_id == current_user.id).all()
    project_ids = [p.id for p in pm_projects]

    # 查询待审批任务
    query = db.query(TaskUnified).filter(
        and_(
            TaskUnified.project_id.in_(project_ids),
            TaskUnified.approval_status == 'PENDING_APPROVAL',
            TaskUnified.approval_required == True
        )
    ).order_by(TaskUnified.created_at.desc())

    try:
        count_result = query.count()
        total = int(count_result) if count_result is not None else 0
    except Exception:
        total = 0
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

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
    pages = (total + page_size - 1) // page_size if total > 0 else 0

    return schemas.TaskListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


@router.put("/tasks/{task_id}/approve", response_model=schemas.TaskApprovalResponse)
def approve_task(
    task_id: int,
    approval_data: schemas.TaskApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    批准任务（PM操作）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证审批权限
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or project.pm_id != current_user.id:
        raise HTTPException(status_code=403, detail="您没有权限审批此任务")

    # 验证任务状态
    if task.approval_status != 'PENDING_APPROVAL':
        raise HTTPException(status_code=400, detail="任务不在待审批状态")

    # 更新任务状态
    task.approval_status = 'APPROVED'
    task.approved_by = current_user.id
    task.approved_at = datetime.now()
    task.approval_note = approval_data.comment
    task.status = 'ACCEPTED'  # 审批通过后，任务可以开始执行
    task.updated_at = datetime.now()

    # 更新审批工作流
    workflow = db.query(TaskApprovalWorkflow).filter(
        and_(
            TaskApprovalWorkflow.task_id == task_id,
            TaskApprovalWorkflow.approval_status == 'PENDING'
        )
    ).first()

    if workflow:
        workflow.approval_status = 'APPROVED'
        workflow.approver_id = current_user.id
        workflow.approved_at = datetime.now()
        workflow.approval_note = approval_data.comment

    db.commit()

    # 发送通知给任务执行人
    from app.services.notification_service import NotificationType, notification_service
    try:
        notification_service.send_notification(
            db=db,
            recipient_id=task.assignee_id,
            notification_type=NotificationType.TASK_APPROVED,
            title=f"任务已审批通过：{task.title or f'任务#{task.id}'}",
            content=f"审批人：{current_user.real_name or current_user.username}\n备注：{approval_data.comment or '无'}",
            priority=notification_service.NotificationPriority.NORMAL,
            link=f"/engineers/tasks/{task.id}"
        )
    except Exception:
        # 通知失败不影响主流程
        logger.warning("工程师任务审批通过通知发送失败，不影响主流程", exc_info=True)

    return schemas.TaskApprovalResponse(
        task_id=task.id,
        status=task.status,
        approval_status=task.approval_status,
        approved_by=current_user.id,
        approved_at=task.approved_at,
        approval_note=task.approval_note
    )


@router.put("/tasks/{task_id}/reject", response_model=schemas.TaskApprovalResponse)
def reject_task(
    task_id: int,
    rejection_data: schemas.TaskRejectionRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    拒绝任务（PM操作）
    """
    # 获取任务
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证审批权限
    project = db.query(Project).filter(Project.id == task.project_id).first()
    if not project or project.pm_id != current_user.id:
        raise HTTPException(status_code=403, detail="您没有权限审批此任务")

    # 验证任务状态
    if task.approval_status != 'PENDING_APPROVAL':
        raise HTTPException(status_code=400, detail="任务不在待审批状态")

    # 更新任务状态
    task.approval_status = 'REJECTED'
    task.approved_by = current_user.id
    task.approved_at = datetime.now()
    task.approval_note = rejection_data.reason
    task.status = 'REJECTED'
    task.updated_at = datetime.now()

    # 更新审批工作流
    workflow = db.query(TaskApprovalWorkflow).filter(
        and_(
            TaskApprovalWorkflow.task_id == task_id,
            TaskApprovalWorkflow.approval_status == 'PENDING'
        )
    ).first()

    if workflow:
        workflow.approval_status = 'REJECTED'
        workflow.approver_id = current_user.id
        workflow.approved_at = datetime.now()
        workflow.rejection_reason = rejection_data.reason

    db.commit()

    # 发送通知给任务创建人
    from app.services.notification_service import NotificationType, notification_service
    try:
        notification_service.send_notification(
            db=db,
            recipient_id=task.created_by,
            notification_type=NotificationType.TASK_REJECTED,
            title=f"任务已被拒绝：{task.title or f'任务#{task.id}'}",
            content=f"审批人：{current_user.real_name or current_user.username}\n拒绝原因：{rejection_data.reason}",
            priority=notification_service.NotificationPriority.HIGH,
            link=f"/engineers/tasks/{task.id}"
        )
    except Exception:
        # 通知失败不影响主流程
        logger.warning("工程师任务审批驳回通知发送失败，不影响主流程", exc_info=True)

    return schemas.TaskApprovalResponse(
        task_id=task.id,
        status=task.status,
        approval_status=task.approval_status,
        approved_by=current_user.id,
        approved_at=task.approved_at,
        approval_note=task.approval_note
    )


@router.get("/tasks/{task_id}/approval-history", response_model=List[dict])
def get_task_approval_history(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("engineer:read"))
):
    """
    获取任务审批历史
    """
    # 验证任务存在
    task = db.query(TaskUnified).filter(TaskUnified.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 验证权限（任务相关人员可查看）
    if task.assignee_id != current_user.id and task.created_by != current_user.id:
        project = db.query(Project).filter(Project.id == task.project_id).first()
        if not project or project.pm_id != current_user.id:
            raise HTTPException(status_code=403, detail="没有权限查看审批历史")

    # 查询审批历史
    workflows = db.query(TaskApprovalWorkflow).filter(
        TaskApprovalWorkflow.task_id == task_id
    ).order_by(TaskApprovalWorkflow.submitted_at.desc()).all()

    # 构建响应
    from app.models.user import User
    history = []
    for wf in workflows:
        submitter = db.query(User).filter(User.id == wf.submitted_by).first()
        approver = db.query(User).filter(User.id == wf.approver_id).first() if wf.approver_id else None

        history.append({
            "id": wf.id,
            "submitted_by": submitter.real_name if submitter else None,
            "submitted_at": wf.submitted_at,
            "submit_note": wf.submit_note,
            "approver": approver.real_name if approver else None,
            "approval_status": wf.approval_status,
            "approved_at": wf.approved_at,
            "approval_note": wf.approval_note,
            "rejection_reason": wf.rejection_reason
        })

    return history
