# -*- coding: utf-8 -*-
"""
项目审批 - cancel

提供cancel相关的审批功能
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



@router.post(
    "/{project_id}/approval/cancel",
    response_model=ApprovalStatusResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_project_approval(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    撤销项目审批（仅发起人可操作）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if project.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="项目不在审批中，无法撤销")

    if not project.approval_record_id:
        raise HTTPException(status_code=400, detail="项目无审批记录")

    approval_record = (
        db.query(ApprovalRecord)
        .filter(ApprovalRecord.id == project.approval_record_id)
        .first()
    )
    if not approval_record:
        raise HTTPException(status_code=400, detail="审批记录不存在")

    # 验证是否为发起人
    if approval_record.initiator_id != current_user.id:
        raise HTTPException(status_code=403, detail="仅发起人可撤销审批")

    # 撤销审批
    approval_record.status = "CANCELLED"
    project.approval_status = "NONE"
    project.approval_record_id = None

    # 记录撤销历史
    history = ApprovalHistory(
        approval_record_id=approval_record.id,
        step_order=approval_record.current_step,
        approver_id=current_user.id,
        action="CANCEL",
        comment="发起人撤销审批",
        action_at=datetime.now(),
    )
    db.add(history)
    db.commit()

    return ApprovalStatusResponse(
        entity_id=project_id,
        entity_type=ENTITY_TYPE_PROJECT,
        workflow_name=None,
        current_step=None,
        current_approver=None,
        status="CANCELLED",
        progress=0,
    )
