# -*- coding: utf-8 -*-
"""
合同审批工作流 API endpoints
包括：审批流程启动、审批操作、审批状态查询、审批历史
"""

import logging
from typing import Any, List

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import (
    ApprovalActionEnum,
    ApprovalRecordStatusEnum,
    ContractStatusEnum,
    WorkflowTypeEnum,
)
from app.models.sales import Contract
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    ApprovalActionRequest,
    ApprovalHistoryResponse,
    ApprovalRecordResponse,
    ApprovalStartRequest,
    ApprovalStatusResponse,
)
from app.services.approval_workflow_service import ApprovalWorkflowService

router = APIRouter()


@router.post("/contracts/{contract_id}/approval/start", response_model=ResponseModel)
def start_contract_approval(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    approval_request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动合同审批流程
    """
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    if contract.status != ContractStatusEnum.DRAFT and contract.status != ContractStatusEnum.IN_REVIEW:
        raise HTTPException(status_code=400, detail="只有草稿或待审批状态的合同才能启动审批流程")

    # 获取合同金额用于路由
    routing_params = {
        "amount": float(contract.contract_amount or 0)
    }

    # 启动审批流程
    workflow_service = ApprovalWorkflowService(db)
    try:
        record = workflow_service.start_approval(
            entity_type=WorkflowTypeEnum.CONTRACT,
            entity_id=contract_id,
            initiator_id=current_user.id,
            workflow_id=approval_request.workflow_id,
            routing_params=routing_params,
            comment=approval_request.comment
        )

        # 更新合同状态
        contract.status = ContractStatusEnum.IN_REVIEW

        db.commit()

        # 发送审批通知给当前审批人
        from app.services.notification_service import (
            NotificationPriority,
            NotificationType,
            notification_service,
        )
        try:
            # 获取当前待审批的步骤
            current_step = workflow_service.get_current_step(record.id)
            if current_step and current_step.get("approver_id"):
                notification_service.send_notification(
                    db=db,
                    recipient_id=current_step["approver_id"],
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"待审批合同: {contract.contract_name}",
                    content=f"合同编码: {contract.contract_no}\n合同金额: ¥{float(contract.contract_amount or 0):,.2f}\n发起人: {current_user.real_name or current_user.username}",
                    priority=NotificationPriority.HIGH,
                    link=f"/sales/contracts/{contract.id}/approval"
                )
        except Exception:
            logger.warning("合同审批启动通知发送失败，不影响主流程", exc_info=True)

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={"approval_record_id": record.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contracts/{contract_id}/approval-status", response_model=ApprovalStatusResponse)
def get_contract_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同审批状态
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.CONTRACT,
        entity_id=contract_id
    )

    if not record:
        return ApprovalStatusResponse(
            record=None,
            current_step_info=None,
            can_approve=False,
            can_reject=False,
            can_delegate=False,
            can_withdraw=False
        )

    current_step_info = workflow_service.get_current_step(record.id)

    can_approve = False
    can_reject = False
    can_delegate = False
    can_withdraw = False

    if record.status == ApprovalRecordStatusEnum.PENDING:
        if current_step_info:
            if current_step_info.get("approver_id") == current_user.id:
                can_approve = True
                can_reject = True
                if current_step_info.get("can_delegate"):
                    can_delegate = True

        if record.initiator_id == current_user.id:
            can_withdraw = True

    record_dict = {
        **{c.name: getattr(record, c.name) for c in record.__table__.columns},
        "workflow_name": record.workflow.workflow_name if record.workflow else None,
        "initiator_name": record.initiator.real_name if record.initiator else None,
        "history": []
    }

    history_list = workflow_service.get_approval_history(record.id)
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        record_dict["history"].append(ApprovalHistoryResponse(**history_dict))

    return ApprovalStatusResponse(
        record=ApprovalRecordResponse(**record_dict),
        current_step_info=current_step_info,
        can_approve=can_approve,
        can_reject=can_reject,
        can_delegate=can_delegate,
        can_withdraw=can_withdraw
    )


@router.post("/contracts/{contract_id}/approval/action", response_model=ResponseModel)
def contract_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同审批操作（通过/驳回/委托/撤回）
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.CONTRACT,
        entity_id=contract_id
    )

    if not record:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            record = workflow_service.approve_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment
            )

            if record.status == ApprovalRecordStatusEnum.APPROVED:
                # 审批完成，允许合同签订
                contract.status = ContractStatusEnum.IN_REVIEW  # 保持待审批状态，等待签订

                # 发送审批完成通知
                from app.services.notification_service import (
                    NotificationPriority,
                    NotificationType,
                    notification_service,
                )
                try:
                    # 通知合同创建人审批已完成
                    notification_service.send_notification(
                        db=db,
                        recipient_id=contract.created_by,
                        notification_type=NotificationType.TASK_APPROVED,
                        title=f"合同审批已完成: {contract.contract_name}",
                        content=f"合同编号: {contract.contract_no}\n审批人: {current_user.real_name or current_user.username}",
                        priority=NotificationPriority.NORMAL,
                        link=f"/sales/contracts/{contract.id}"
                    )
                except Exception:
                    logger.warning("合同审批完成通知发送失败，不影响主流程", exc_info=True)
            message = "审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            record = workflow_service.reject_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回"
            )
            contract.status = ContractStatusEnum.CANCELLED
            message = "审批已驳回"

            # 发送驳回通知
            from app.services.notification_service import (
                NotificationPriority,
                NotificationType,
                notification_service,
            )
            try:
                notification_service.send_notification(
                    db=db,
                    recipient_id=contract.created_by,
                    notification_type=NotificationType.TASK_REJECTED,
                    title=f"合同审批已驳回: {contract.contract_name}",
                    content=f"合同编号: {contract.contract_no}\n驳回原因: {action_request.comment or '无'}",
                    priority=NotificationPriority.HIGH,
                    link=f"/sales/contracts/{contract.id}"
                )
            except Exception:
                logger.warning("合同审批驳回通知发送失败，不影响主流程", exc_info=True)

        elif action_request.action == ApprovalActionEnum.DELEGATE:
            if not action_request.delegate_to_id:
                raise HTTPException(status_code=400, detail="委托操作需要指定委托给的用户ID")

            record = workflow_service.delegate_step(
                record_id=record.id,
                approver_id=current_user.id,
                delegate_to_id=action_request.delegate_to_id,
                comment=action_request.comment
            )
            message = "审批已委托"

            # 发送委托通知
            from app.services.notification_service import (
                NotificationType,
                notification_service,
            )
            try:
                notification_service.send_notification(
                    db=db,
                    recipient_id=action_request.delegate_to_id,
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"合同审批已委托给您: {contract.contract_name}",
                    content=f"原审批人: {current_user.real_name or current_user.username}\n合同编码: {contract.contract_no}",
                    priority=notification_service.NotificationPriority.NORMAL,
                    link=f"/sales/contracts/{contract.id}/approval"
                )
            except Exception:
                logger.warning("合同审批委托通知发送失败，不影响主流程", exc_info=True)

        elif action_request.action == ApprovalActionEnum.WITHDRAW:
            record = workflow_service.withdraw_approval(
                record_id=record.id,
                initiator_id=current_user.id,
                comment=action_request.comment
            )
            contract.status = ContractStatusEnum.DRAFT
            message = "审批已撤回"

        else:
            raise HTTPException(status_code=400, detail=f"不支持的审批操作: {action_request.action}")

        db.commit()

        return ResponseModel(
            code=200,
            message=message,
            data={"approval_record_id": record.id, "status": record.status}
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/contracts/{contract_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_contract_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取合同审批历史
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.CONTRACT,
        entity_id=contract_id
    )

    if not record:
        return []

    history_list = workflow_service.get_approval_history(record.id)
    result = []
    for h in history_list:
        history_dict = {
            **{c.name: getattr(h, c.name) for c in h.__table__.columns},
            "approver_name": h.approver.real_name if h.approver else None,
            "delegate_to_name": h.delegate_to.real_name if h.delegate_to else None
        }
        result.append(ApprovalHistoryResponse(**history_dict))

    return result


# ==================== 简单审批（兼容旧接口） ====================


@router.put("/contracts/{contract_id}/approve", response_model=ResponseModel)
def approve_contract(
    *,
    db: Session = Depends(deps.get_db),
    contract_id: int,
    approved: bool = Query(..., description="是否批准"),
    remark: Any = Query(None, description="审批意见"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    合同审批
    """
    # 检查审批权限
    if not security.has_sales_approval_access(current_user, db):
        raise HTTPException(
            status_code=403,
            detail="您没有权限审批合同"
        )

    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合同不存在")

    if approved:
        contract.status = "APPROVED"
    else:
        contract.status = "REJECTED"

    db.commit()

    return ResponseModel(code=200, message="合同审批完成" if approved else "合同已驳回")
