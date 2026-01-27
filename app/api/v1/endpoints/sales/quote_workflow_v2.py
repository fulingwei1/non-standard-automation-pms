# -*- coding: utf-8 -*-
"""
报价工作流操作（基于统一状态机框架）

包含：提交审批、审批操作、发送客户、客户反馈、转换合同等流程控制
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.quote import QuoteStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
    StateMachineValidationError,
)
from app.models.sales.quotes import Quote
from app.models.user import User
from app.schemas.sales.quotes import QuoteResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/quotes/{quote_id}/submit/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def submit_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approver_ids: list[int] = Query(None, description="审批人ID列表"),
    current_user: User = Depends(security.require_permission("quote:submit")),
) -> Any:
    """
    提交报价审批（使用状态机框架）

    状态转换: DRAFT → PENDING_APPROVAL
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "PENDING_APPROVAL",
            current_user=current_user,
            comment="提交报价审批",
            approver_ids=approver_ids,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except StateMachineValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/quotes/{quote_id}/withdraw/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def withdraw_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    撤回报价审批（使用状态机框架）

    状态转换: PENDING_APPROVAL → DRAFT
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "DRAFT",
            current_user=current_user,
            comment="撤回报价审批",
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/approve/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def approve_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    approval_opinion: str = Query(None, description="审批意见"),
    from_review: bool = Query(False, description="是否从评审中批准"),
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    批准报价（使用状态机框架）

    状态转换:
    - PENDING_APPROVAL → APPROVED (快速批准)
    - IN_REVIEW → APPROVED (评审后批准)
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "APPROVED",
            current_user=current_user,
            comment=f"批准报价: {approval_opinion or ''}",
            approval_opinion=approval_opinion,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/reject/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def reject_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    rejection_reason: str = Query(..., description="拒绝原因"),
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    拒绝报价（使用状态机框架）

    状态转换:
    - PENDING_APPROVAL → REJECTED
    - IN_REVIEW → REJECTED
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "REJECTED",
            current_user=current_user,
            comment=f"拒绝报价: {rejection_reason}",
            rejection_reason=rejection_reason,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/send/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def send_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    sent_to: str = Query(..., description="发送对象"),
    sent_via: str = Query("EMAIL", description="发送方式"),
    current_user: User = Depends(security.require_permission("quote:send")),
) -> Any:
    """
    发送报价给客户（使用状态机框架）

    状态转换: APPROVED → SENT
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "SENT",
            current_user=current_user,
            comment=f"发送报价给 {sent_to}",
            sent_to=sent_to,
            sent_via=sent_via,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/accept/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def accept_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    acceptance_note: str = Query(None, description="接受说明"),
    current_user: User = Depends(security.require_permission("quote:accept")),
) -> Any:
    """
    客户接受报价（使用状态机框架）

    状态转换: SENT → ACCEPTED
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "ACCEPTED",
            current_user=current_user,
            comment="客户接受报价",
            acceptance_note=acceptance_note,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/convert/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def convert_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    contract_id: int = Query(..., description="合同ID"),
    current_user: User = Depends(security.require_permission("quote:convert")),
) -> Any:
    """
    转换为合同（使用状态机框架）

    状态转换: ACCEPTED → CONVERTED
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "CONVERTED",
            current_user=current_user,
            comment=f"转换为合同 {contract_id}",
            contract_id=contract_id,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/cancel/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    cancellation_reason: str = Query(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消报价（使用状态机框架）

    状态转换:
    - DRAFT → CANCELLED
    - APPROVED → CANCELLED
    - REJECTED → CANCELLED
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "CANCELLED",
            current_user=current_user,
            comment=f"取消报价: {cancellation_reason or ''}",
            cancellation_reason=cancellation_reason,
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.post(
    "/quotes/{quote_id}/expire/v2",
    response_model=QuoteResponse,
    status_code=status.HTTP_200_OK,
)
def expire_quote_v2(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价过期（使用状态机框架）

    状态转换:
    - APPROVED → EXPIRED
    - SENT → EXPIRED
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    state_machine = QuoteStateMachine(quote, db)

    try:
        state_machine.transition_to(
            "EXPIRED",
            current_user=current_user,
            comment="报价已过期",
        )

        db.commit()
        db.refresh(quote)

        return quote

    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
