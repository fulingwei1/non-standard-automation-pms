# -*- coding: utf-8 -*-
"""
项目审批 - status

提供status相关的审批功能
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.sales.workflow import ApprovalRecord, ApprovalWorkflow, ApprovalWorkflowStep
from app.models.user import User
from app.schemas.sales.contracts import ApprovalStatusResponse, ApprovalHistoryResponse

from .utils import ENTITY_TYPE_PROJECT, get_user_display_name

logger = logging.getLogger(__name__)

router = APIRouter()


router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"



@router.get(
    "/{project_id}/approval/status",
    response_model=ApprovalStatusResponse,
    status_code=status.HTTP_200_OK,
)
def get_project_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目审批状态
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if not project.approval_record_id:
        return ApprovalStatusResponse(
            entity_id=project_id,
            entity_type=ENTITY_TYPE_PROJECT,
            workflow_name=None,
            current_step=None,
            current_approver=None,
            status=project.approval_status or "NONE",
            progress=0,
        )

    approval_record = (
        db.query(ApprovalRecord)
        .filter(ApprovalRecord.id == project.approval_record_id)
        .first()
    )
    if not approval_record:
        return ApprovalStatusResponse(
            entity_id=project_id,
            entity_type=ENTITY_TYPE_PROJECT,
            workflow_name=None,
            current_step=None,
            current_approver=None,
            status=project.approval_status or "NONE",
            progress=0,
        )

    workflow = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.id == approval_record.workflow_id)
        .first()
    )
    workflow_name = workflow.workflow_name if workflow else None

    steps = (
        db.query(ApprovalWorkflowStep)
        .filter(ApprovalWorkflowStep.workflow_id == approval_record.workflow_id)
        .order_by(ApprovalWorkflowStep.step_order)
        .all()
    )
    total_steps = len(steps)

    if approval_record.status in ["APPROVED", "REJECTED", "CANCELLED"]:
        progress = 100 if approval_record.status == "APPROVED" else int(
            (approval_record.current_step - 1) / total_steps * 100
        ) if total_steps > 0 else 0
        return ApprovalStatusResponse(
            entity_id=project_id,
            entity_type=ENTITY_TYPE_PROJECT,
            workflow_name=workflow_name,
            current_step="已完成" if approval_record.status == "APPROVED" else "已终止",
            current_approver=None,
            status=approval_record.status,
            progress=progress,
        )

    current_step_index = approval_record.current_step - 1
    if current_step_index < total_steps:
        current_step = steps[current_step_index]
        current_approver = get_user_display_name(db, current_step.approver_id)
        if not current_approver and current_step.approver_role:
            current_approver = f"角色: {current_step.approver_role}"
        progress = int((approval_record.current_step - 1) / total_steps * 100) if total_steps > 0 else 0
    else:
        current_step = None
        current_approver = None
        progress = 100

    return ApprovalStatusResponse(
        entity_id=project_id,
        entity_type=ENTITY_TYPE_PROJECT,
        workflow_name=workflow_name,
        current_step=current_step.step_name if current_step else None,
        current_approver=current_approver,
        status=approval_record.status,
        progress=progress,
    )


