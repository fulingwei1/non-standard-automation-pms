# -*- coding: utf-8 -*-
"""
发票工作流审批 API endpoints (新版)
"""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import (
    ApprovalActionEnum,
    ApprovalRecordStatusEnum,
    InvoiceStatusEnum,
    WorkflowTypeEnum,
)
from app.models.sales import Invoice
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    ApprovalActionRequest,
    ApprovalHistoryResponse,
    ApprovalRecordResponse,
    ApprovalStartRequest,
    ApprovalStatusResponse,
)
from app.services.approval_engine import ApprovalEngineService as ApprovalWorkflowService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/invoices/{invoice_id}/approval/start", response_model=ResponseModel)
def start_invoice_approval(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    approval_request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动发票审批流程
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    if invoice.status != InvoiceStatusEnum.APPLIED:
        raise HTTPException(status_code=400, detail="只有已申请状态的发票才能启动审批流程")

    # 获取发票金额用于路由
    routing_params = {
        "amount": float(invoice.amount or 0)
    }

    # 启动审批流程
    workflow_service = ApprovalWorkflowService(db)
    try:
        record = workflow_service.start_approval(
            entity_type=WorkflowTypeEnum.INVOICE,
            entity_id=invoice_id,
            initiator_id=current_user.id,
            workflow_id=approval_request.workflow_id,
            routing_params=routing_params,
            comment=approval_request.comment
        )

        # 更新发票状态
        invoice.status = InvoiceStatusEnum.IN_REVIEW

        db.commit()

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={"approval_record_id": record.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/invoices/{invoice_id}/approval-status", response_model=ApprovalStatusResponse)
def get_invoice_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批状态
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
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


@router.post("/invoices/{invoice_id}/approval/action", response_model=ResponseModel)
def invoice_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发票审批操作（通过/驳回/委托/撤回）
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
    )

    if not record:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="发票不存在")

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            record = workflow_service.approve_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment
            )

            if record.status == ApprovalRecordStatusEnum.APPROVED:
                # 审批完成，允许开票
                invoice.status = InvoiceStatusEnum.APPROVED
            message = "审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            record = workflow_service.reject_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回"
            )
            invoice.status = InvoiceStatusEnum.REJECTED
            message = "审批已驳回"

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

        elif action_request.action == ApprovalActionEnum.WITHDRAW:
            record = workflow_service.withdraw_approval(
                record_id=record.id,
                initiator_id=current_user.id,
                comment=action_request.comment
            )
            invoice.status = InvoiceStatusEnum.APPLIED
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


@router.get("/invoices/{invoice_id}/approval-history", response_model=List[ApprovalHistoryResponse])
def get_invoice_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    invoice_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取发票审批历史
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.INVOICE,
        entity_id=invoice_id
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
