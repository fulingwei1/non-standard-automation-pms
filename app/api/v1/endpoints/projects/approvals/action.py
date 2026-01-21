# -*- coding: utf-8 -*-
"""
项目审批 - action

提供action相关的审批功能
"""

"""
项目审批管理 API endpoints

包含：提交审批、审批通过/驳回、查看审批状态、审批历史
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.sales.workflow import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
)
from app.models.user import User
from app.schemas.sales.contracts import (
    ApprovalActionRequest,
    ApprovalHistoryResponse,
    ApprovalRecordResponse,
    ApprovalStartRequest,
    ApprovalStatusResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 项目审批的实体类型常量
ENTITY_TYPE_PROJECT = "PROJECT"



@router.post(
    "/{project_id}/approval/action",
    response_model=ApprovalStatusResponse,
    status_code=status.HTTP_200_OK,
)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    执行审批动作

    - APPROVE: 审批通过，进入下一步或完成
    - REJECT: 审批驳回
    - RETURN: 退回上一步
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    if project.approval_status != "PENDING":
        raise HTTPException(status_code=400, detail="项目不在审批中")

    if not project.approval_record_id:
        raise HTTPException(status_code=400, detail="项目无审批记录")

    approval_record = (
        db.query(ApprovalRecord)
        .filter(ApprovalRecord.id == project.approval_record_id)
        .first()
    )
    if not approval_record:
        raise HTTPException(status_code=400, detail="审批记录不存在")

    # 获取工作流步骤
    steps = (
        db.query(ApprovalWorkflowStep)
        .filter(ApprovalWorkflowStep.workflow_id == approval_record.workflow_id)
        .order_by(ApprovalWorkflowStep.step_order)
        .all()
    )
    total_steps = len(steps)
    current_step_index = approval_record.current_step - 1

    if current_step_index >= total_steps:
        raise HTTPException(status_code=400, detail="审批步骤异常")

    current_step = steps[current_step_index]

    # 验证当前用户是否有权限审批
    has_permission = _check_approval_permission(db, current_user, current_step)
    if not has_permission:
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批此步骤。需要指定审批人或具有相应角色。"
        )

    # 记录审批历史
    history = ApprovalHistory(
        approval_record_id=approval_record.id,
        step_order=approval_record.current_step,
        approver_id=current_user.id,
        action=request.action.upper(),
        comment=request.comment,
        action_at=datetime.now(),
    )
    db.add(history)

    workflow = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.id == approval_record.workflow_id)
        .first()
    )
    workflow_name = workflow.workflow_name if workflow else "未知工作流"

    if request.action.upper() == "APPROVE":
        if approval_record.current_step >= total_steps:
            # 最后一步通过，审批完成
            approval_record.status = "APPROVED"
            project.approval_status = "APPROVED"
            db.commit()
            return ApprovalStatusResponse(
                entity_id=project_id,
                entity_type=ENTITY_TYPE_PROJECT,
                workflow_name=workflow_name,
                current_step="已完成",
                current_approver=None,
                status="APPROVED",
                progress=100,
            )
        else:
            # 进入下一步
            approval_record.current_step += 1
            db.commit()

            next_step = steps[approval_record.current_step - 1]
            next_approver = get_user_display_name(db, next_step.approver_id)
            if not next_approver and next_step.approver_role:
                next_approver = f"角色: {next_step.approver_role}"

            progress = int((approval_record.current_step - 1) / total_steps * 100)
            return ApprovalStatusResponse(
                entity_id=project_id,
                entity_type=ENTITY_TYPE_PROJECT,
                workflow_name=workflow_name,
                current_step=next_step.step_name,
                current_approver=next_approver,
                status="PENDING",
                progress=progress,
            )

    elif request.action.upper() == "REJECT":
        approval_record.status = "REJECTED"
        project.approval_status = "REJECTED"
        db.commit()
        return ApprovalStatusResponse(
            entity_id=project_id,
            entity_type=ENTITY_TYPE_PROJECT,
            workflow_name=workflow_name,
            current_step=current_step.step_name,
            current_approver=None,
            status="REJECTED",
            progress=int((approval_record.current_step - 1) / total_steps * 100),
        )

    elif request.action.upper() == "RETURN":
        if approval_record.current_step <= 1:
            raise HTTPException(status_code=400, detail="已是第一步，无法退回")
        approval_record.current_step -= 1
        db.commit()

        prev_step = steps[approval_record.current_step - 1]
        prev_approver = get_user_display_name(db, prev_step.approver_id)
        if not prev_approver and prev_step.approver_role:
            prev_approver = f"角色: {prev_step.approver_role}"

        progress = int((approval_record.current_step - 1) / total_steps * 100)
        return ApprovalStatusResponse(
            entity_id=project_id,
            entity_type=ENTITY_TYPE_PROJECT,
            workflow_name=workflow_name,
            current_step=prev_step.step_name,
            current_approver=prev_approver,
            status="PENDING",
            progress=progress,
        )

    else:
        raise HTTPException(status_code=400, detail="无效的审批动作")


