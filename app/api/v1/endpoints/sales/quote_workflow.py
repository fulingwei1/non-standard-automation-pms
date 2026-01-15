# -*- coding: utf-8 -*-
"""
审批工作流 - 自动生成
从 sales/quotes.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.sales import (

from app.schemas.sales import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/quotes/{quote_id}/approval",
    tags=["workflow"]
)

# 共 3 个路由

# ==================== 审批工作流 ====================


@router.post("/quotes/{quote_id}/approval/start", response_model=ResponseModel)
def start_quote_approval(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_request: ApprovalStartRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    启动报价审批流程
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != QuoteStatusEnum.IN_REVIEW:
        raise HTTPException(status_code=400, detail="只有待审批状态的报价才能启动审批流程")

    # 获取报价金额用于路由
    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    routing_params = {
        "amount": float(version.total_price or 0) if version else 0
    }

    # 启动审批流程
    workflow_service = ApprovalWorkflowService(db)
    try:
        record = workflow_service.start_approval(
            entity_type=WorkflowTypeEnum.QUOTE,
            entity_id=quote_id,
            initiator_id=current_user.id,
            workflow_id=approval_request.workflow_id,
            routing_params=routing_params,
            comment=approval_request.comment
        )

        # 更新报价状态
        quote.status = QuoteStatusEnum.IN_REVIEW

        db.commit()

        return ResponseModel(
            code=200,
            message="审批流程已启动",
            data={"approval_record_id": record.id}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quotes/{quote_id}/approval-status", response_model=ApprovalStatusResponse)
def get_quote_approval_status(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价审批状态
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.QUOTE,
        entity_id=quote_id
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

    # 获取当前步骤信息
    current_step_info = workflow_service.get_current_step(record.id)

    # 判断当前用户的操作权限
    can_approve = False
    can_reject = False
    can_delegate = False
    can_withdraw = False

    if record.status == ApprovalRecordStatusEnum.PENDING:
        if current_step_info:
            # 检查是否是当前审批人
            if current_step_info.get("approver_id") == current_user.id:
                can_approve = True
                can_reject = True
                if current_step_info.get("can_delegate"):
                    can_delegate = True

        # 检查是否可以撤回（只有发起人可以撤回）
        if record.initiator_id == current_user.id:
            can_withdraw = True

    # 构建响应
    record_dict = {
        **{c.name: getattr(record, c.name) for c in record.__table__.columns},
        "workflow_name": record.workflow.workflow_name if record.workflow else None,
        "initiator_name": record.initiator.real_name if record.initiator else None,
        "history": []
    }

    # 获取审批历史
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


@router.post("/quotes/{quote_id}/approval/action", response_model=ResponseModel)
def quote_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    action_request: ApprovalActionRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价审批操作（通过/驳回/委托/撤回）
    """
    workflow_service = ApprovalWorkflowService(db)
    record = workflow_service.get_approval_record(
        entity_type=WorkflowTypeEnum.QUOTE,
        entity_id=quote_id
    )

    if not record:
        raise HTTPException(status_code=404, detail="审批记录不存在")

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    try:
        if action_request.action == ApprovalActionEnum.APPROVE:
            record = workflow_service.approve_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment
            )

            # 如果审批完成，更新报价状态
            if record.status == ApprovalRecordStatusEnum.APPROVED:
                quote.status = QuoteStatusEnum.APPROVED
                version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
                if version:
                    version.approved_by = current_user.id
                    version.approved_at = datetime.now()

            message = "审批通过"

        elif action_request.action == ApprovalActionEnum.REJECT:
            record = workflow_service.reject_step(
                record_id=record.id,
                approver_id=current_user.id,
                comment=action_request.comment or "审批驳回"
            )

            # 驳回后更新报价状态
            quote.status = QuoteStatusEnum.REJECTED
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

            # 撤回后恢复报价状态
            quote.status = QuoteStatusEnum.DRAFT
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



