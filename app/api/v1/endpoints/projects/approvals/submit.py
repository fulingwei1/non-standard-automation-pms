# -*- coding: utf-8 -*-
"""
项目审批 - submit

提供submit相关的审批功能
"""

"""
项目审批管理 API endpoints

包含：提交审批、审批通过/驳回、查看审批状态、审批历史
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.sales.workflow import (
    ApprovalRecord,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
)
from app.models.user import User
from app.schemas.sales.contracts import (
    ApprovalStartRequest,
    ApprovalStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"


@router.post(
    "/approval/submit",
    response_model=ApprovalStatusResponse,
    status_code=status.HTTP_200_OK,
)
def submit_project_approval(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交项目审批

    - 选择审批工作流
    - 创建审批记录
    - 更新项目审批状态
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 检查项目状态
    if project.approval_status == "PENDING":
        raise HTTPException(status_code=400, detail="项目已在审批中")
    if project.approval_status == "APPROVED":
        raise HTTPException(status_code=400, detail="项目已审批通过")

    # 获取审批工作流
    workflow = None
    if request.workflow_id:
        workflow = (
            db.query(ApprovalWorkflow)
            .filter(
                ApprovalWorkflow.id == request.workflow_id,
                ApprovalWorkflow.is_active == True,
            )
            .first()
        )
    else:
        # 查找项目类型的默认工作流
        workflow = (
            db.query(ApprovalWorkflow)
            .filter(
                ApprovalWorkflow.workflow_type == ENTITY_TYPE_PROJECT,
                ApprovalWorkflow.is_active == True,
            )
            .first()
        )

    if not workflow:
        raise HTTPException(status_code=400, detail="未找到可用的审批工作流")

    # 检查工作流是否有步骤
    steps = (
        db.query(ApprovalWorkflowStep)
        .filter(ApprovalWorkflowStep.workflow_id == workflow.id)
        .order_by(ApprovalWorkflowStep.step_order)
        .all()
    )
    if not steps:
        raise HTTPException(status_code=400, detail="审批工作流未配置审批步骤")

    # 创建审批记录
    approval_record = ApprovalRecord(
        entity_type=ENTITY_TYPE_PROJECT,
        entity_id=project_id,
        workflow_id=workflow.id,
        current_step=1,
        status="PENDING",
        initiator_id=current_user.id,
    )
    db.add(approval_record)
    db.flush()

    # 更新项目审批状态
    project.approval_status = "PENDING"
    project.approval_record_id = approval_record.id

    db.commit()

    # 获取当前步骤信息
    current_step = steps[0]
    current_approver = get_user_display_name(db, current_step.approver_id)
    if not current_approver and current_step.approver_role:
        current_approver = f"角色: {current_step.approver_role}"

    return ApprovalStatusResponse(
        entity_id=project_id,
        entity_type=ENTITY_TYPE_PROJECT,
        workflow_name=workflow.workflow_name,
        current_step=current_step.step_name,
        current_approver=current_approver,
        status="PENDING",
        progress=0,
    )
