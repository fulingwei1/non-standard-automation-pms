# -*- coding: utf-8 -*-
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


def get_user_display_name(db: Session, user_id: Optional[int]) -> Optional[str]:
    """获取用户显示名称"""
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user.display_name if user else None


def _check_approval_permission(
    db: Session,
    current_user: User,
    step: ApprovalWorkflowStep
) -> bool:
    """
    检查当前用户是否有权限审批该步骤

    Args:
        db: 数据库会话
        current_user: 当前用户
        step: 审批步骤

    Returns:
        是否有权限审批
    """
    # 超级管理员始终有权限
    if current_user.is_superuser:
        return True

    # 1. 检查是否是指定审批人
    if step.approver_id:
        if current_user.id == step.approver_id:
            return True

    # 2. 检查是否具有审批角色
    if step.approver_role:
        from app.models.user import Role, UserRole

        # 查询用户是否具有该角色
        user_has_role = (
            db.query(UserRole)
            .join(Role, UserRole.role_id == Role.id)
            .filter(
                UserRole.user_id == current_user.id,
                Role.role_code == step.approver_role,
                Role.is_active == True,
            )
            .first()
        )

        if user_has_role:
            return True

    # 3. 如果步骤既没有指定审批人也没有指定角色，则所有人都可以审批（向后兼容）
    if not step.approver_id and not step.approver_role:
        logger.warning(f"审批步骤 {step.step_name} 未配置审批人或角色，允许任何用户审批")
        return True

    return False


@router.post(
    "/{project_id}/approval/submit",
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
