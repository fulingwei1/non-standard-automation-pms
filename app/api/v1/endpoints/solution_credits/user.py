# -*- coding: utf-8 -*-
"""
方案生成积分管理 - 用户端API
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.services.solution_credit_service import SolutionCreditService

from .schemas import (
    CreditInfoResponse,
    OperationResponse,
    TransactionListResponse,
    TransactionResponse,
)

router = APIRouter()


@router.get("/my-credits", response_model=CreditInfoResponse)
async def get_my_credits(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    获取当前用户积分信息

    返回当前积分余额、是否可以生成方案等信息
    """
    service = SolutionCreditService(db)
    info = service.get_user_credit_info(current_user.id)

    if not info:
        raise HTTPException(status_code=404, detail="用户不存在")

    return CreditInfoResponse(**info)


@router.get("/my-transactions", response_model=TransactionListResponse)
async def get_my_transactions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    transaction_type: Optional[str] = Query(None, description="交易类型过滤"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    获取当前用户积分交易历史
    """
    service = SolutionCreditService(db)
    transactions, total = service.get_transaction_history(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type
    )

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post("/check-can-generate", response_model=OperationResponse)
async def check_can_generate(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    检查当前用户是否可以生成方案

    前端在用户点击"生成方案"按钮前调用此接口
    """
    service = SolutionCreditService(db)
    can_generate, message = service.can_generate_solution(current_user.id)

    return OperationResponse(
        success=can_generate,
        message=message,
        data={"can_generate": can_generate}
    )
