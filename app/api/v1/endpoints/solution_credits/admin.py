# -*- coding: utf-8 -*-
"""
方案生成积分管理 - 管理员API
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.services.solution_credit_service import SolutionCreditService

from .schemas import (
    AdminAddCreditsRequest,
    AdminDeductCreditsRequest,
    BatchAddCreditsRequest,
    CreditConfigItem,
    CreditInfoResponse,
    OperationResponse,
    TransactionListResponse,
    TransactionResponse,
    UpdateConfigRequest,
    UserCreditItem,
    UserCreditListResponse,
)

router = APIRouter()


# ==================== 用户积分管理 ====================

@router.get("/admin/users", response_model=UserCreditListResponse)
async def admin_get_all_users_credits(
    pagination: PaginationParams = Depends(get_pagination_query),
    search: Optional[str] = Query(None, description="搜索（用户名/姓名/工号）"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】获取所有用户积分列表
    """
    service = SolutionCreditService(db)
    users, total = service.get_all_users_credits(
        page=pagination.page,
        page_size=pagination.page_size,
        search=search
    )

    return UserCreditListResponse(
        items=[UserCreditItem(**u) for u in users],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.get("/admin/user/{user_id}", response_model=CreditInfoResponse)
async def admin_get_user_credits(
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】获取指定用户积分信息
    """
    service = SolutionCreditService(db)
    info = service.get_user_credit_info(user_id)

    if not info:
        raise HTTPException(status_code=404, detail="用户不存在")

    return CreditInfoResponse(**info)


@router.get("/admin/user/{user_id}/transactions", response_model=TransactionListResponse)
async def admin_get_user_transactions(
    user_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    transaction_type: Optional[str] = Query(None, description="交易类型过滤"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】获取指定用户积分交易历史
    """
    service = SolutionCreditService(db)
    transactions, total = service.get_transaction_history(
        user_id=user_id,
        page=pagination.page,
        page_size=pagination.page_size,
        transaction_type=transaction_type
    )

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )


@router.post("/admin/add-credits", response_model=OperationResponse)
async def admin_add_credits(
    request: AdminAddCreditsRequest,
    req: Request,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】给用户充值积分
    """
    service = SolutionCreditService(db)
    success, message, transaction = service.admin_add_credits(
        user_id=request.user_id,
        amount=request.amount,
        operator_id=current_user.id,
        remark=request.remark,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent")
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


@router.post("/admin/batch-add-credits", response_model=OperationResponse)
async def admin_batch_add_credits(
    request: BatchAddCreditsRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】批量充值积分
    """
    service = SolutionCreditService(db)
    result = service.batch_add_credits(
        user_ids=request.user_ids,
        amount=request.amount,
        operator_id=current_user.id,
        remark=request.remark
    )

    return OperationResponse(
        success=result["success_count"] > 0,
        message=f"批量充值完成：成功 {result['success_count']} 人，失败 {result['fail_count']} 人",
        data=result
    )


@router.post("/admin/deduct-credits", response_model=OperationResponse)
async def admin_deduct_credits(
    request: AdminDeductCreditsRequest,
    req: Request,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】扣除用户积分
    """
    service = SolutionCreditService(db)
    success, message, transaction = service.admin_deduct_credits(
        user_id=request.user_id,
        amount=request.amount,
        operator_id=current_user.id,
        remark=request.remark,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent")
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


# ==================== 配置管理API ====================

@router.get("/admin/configs", response_model=List[CreditConfigItem])
async def admin_get_configs(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】获取积分系统配置
    """
    service = SolutionCreditService(db)
    configs = service.get_all_configs()
    return [CreditConfigItem(**c) for c in configs]


@router.put("/admin/configs", response_model=OperationResponse)
async def admin_update_config(
    request: UpdateConfigRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】更新积分系统配置
    """
    service = SolutionCreditService(db)
    success, message = service.update_config(
        key=request.key,
        value=request.value,
        description=request.description
    )

    return OperationResponse(success=success, message=message)
