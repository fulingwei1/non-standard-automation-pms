# -*- coding: utf-8 -*-
"""
方案生成积分管理 - 内部调用API
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.services.solution_credit_service import SolutionCreditService

from .schemas import OperationResponse

router = APIRouter()


@router.post("/internal/deduct-for-generation", response_model=OperationResponse)
async def internal_deduct_for_generation(
    related_type: str = Query(..., description="关联类型，如 lead"),
    related_id: int = Query(..., description="关联ID"),
    remark: Optional[str] = Query(None, description="备注"),
    req: Request = None,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    【内部调用】生成方案时扣除积分

    此接口由方案生成服务内部调用
    """
    service = SolutionCreditService(db)
    success, message, transaction = service.deduct_for_generation(
        user_id=current_user.id,
        related_type=related_type,
        related_id=related_id,
        remark=remark,
        ip_address=req.client.host if req and req.client else None,
        user_agent=req.headers.get("user-agent") if req else None
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return OperationResponse(
        success=True,
        message=message,
        data={
            "transaction_id": transaction.id if transaction else None,
            "new_balance": transaction.balance_after if transaction else None
        }
    )


@router.post("/internal/refund", response_model=OperationResponse)
async def internal_refund_credits(
    related_type: str = Query(..., description="关联类型"),
    related_id: int = Query(..., description="关联ID"),
    amount: Optional[int] = Query(None, description="退还数量，默认为生成消耗数"),
    remark: Optional[str] = Query(None, description="备注"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    【内部调用】退还积分（生成失败时）
    """
    service = SolutionCreditService(db)
    success, message, transaction = service.refund_credits(
        user_id=current_user.id,
        amount=amount,
        related_type=related_type,
        related_id=related_id,
        remark=remark
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return OperationResponse(
        success=True,
        message=message,
        data={
            "transaction_id": transaction.id if transaction else None,
            "new_balance": transaction.balance_after if transaction else None
        }
    )
