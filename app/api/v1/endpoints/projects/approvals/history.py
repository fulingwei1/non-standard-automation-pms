# -*- coding: utf-8 -*-
"""
项目审批 - history

提供history相关的审批功能
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.sales.workflow import ApprovalHistory, ApprovalRecord, ApprovalWorkflow, ApprovalWorkflowStep
from app.models.user import User
from app.schemas.sales.contracts import ApprovalHistoryResponse

from .utils import ENTITY_TYPE_PROJECT, get_user_display_name

logger = logging.getLogger(__name__)

router = APIRouter()



@router.get(
    "/{project_id}/approval/history",
    response_model=ApprovalHistoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_project_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目审批历史
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    records = []
    if project.approval_record_id:
        histories = (
            db.query(ApprovalHistory)
            .filter(ApprovalHistory.approval_record_id == project.approval_record_id)
            .order_by(ApprovalHistory.step_order, ApprovalHistory.action_at)
            .all()
        )

        # 获取工作流步骤名称
        approval_record = (
            db.query(ApprovalRecord)
            .filter(ApprovalRecord.id == project.approval_record_id)
            .first()
        )
        step_names = {}
        if approval_record:
            steps = (
                db.query(ApprovalWorkflowStep)
                .filter(ApprovalWorkflowStep.workflow_id == approval_record.workflow_id)
                .all()
            )
            step_names = {step.step_order: step.step_name for step in steps}

        for h in histories:
            records.append(
                ApprovalRecordResponse(
                    id=h.id,
                    step_name=step_names.get(h.step_order, f"步骤{h.step_order}"),
                    approver_id=h.approver_id,
                    approver_name=get_user_display_name(db, h.approver_id),
                    status=None,
                    action=h.action,
                    comment=h.comment,
                    approved_at=h.action_at,
                    created_at=h.created_at,
                    updated_at=h.updated_at,
                )
            )

    return ApprovalHistoryResponse(
        entity_id=project_id,
        entity_type=ENTITY_TYPE_PROJECT,
        records=records,
    )


