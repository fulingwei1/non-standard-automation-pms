# -*- coding: utf-8 -*-
"""
方案生成积分管理API

提供积分查询、充值、扣除等功能
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.services.solution_credit_service import SolutionCreditService, CreditTransactionType

router = APIRouter()


# ==================== Schema定义 ====================

class CreditInfoResponse(BaseModel):
    """用户积分信息响应"""
    user_id: int
    balance: int = Field(..., description="当前积分余额")
    generate_cost: int = Field(..., description="每次生成消耗积分")
    can_generate: bool = Field(..., description="是否可以生成方案")
    remaining_generations: int = Field(..., description="剩余可生成次数")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")


class TransactionResponse(BaseModel):
    """交易记录响应"""
    id: int
    transaction_type: str
    amount: int
    balance_before: int
    balance_after: int
    related_type: Optional[str]
    related_id: Optional[int]
    remark: Optional[str]
    operator_id: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    """交易记录列表响应"""
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int


class AdminAddCreditsRequest(BaseModel):
    """管理员充值请求"""
    user_id: int = Field(..., description="目标用户ID")
    amount: int = Field(..., ge=1, le=1000, description="充值数量（1-1000）")
    remark: Optional[str] = Field(None, max_length=200, description="充值备注")


class BatchAddCreditsRequest(BaseModel):
    """批量充值请求"""
    user_ids: List[int] = Field(..., min_items=1, max_items=100, description="用户ID列表")
    amount: int = Field(..., ge=1, le=1000, description="每人充值数量（1-1000）")
    remark: Optional[str] = Field(None, max_length=200, description="充值备注")


class AdminDeductCreditsRequest(BaseModel):
    """管理员扣除请求"""
    user_id: int = Field(..., description="目标用户ID")
    amount: int = Field(..., ge=1, le=1000, description="扣除数量（1-1000）")
    remark: str = Field(..., min_length=2, max_length=200, description="扣除原因（必填）")


class UserCreditItem(BaseModel):
    """用户积分项"""
    user_id: int
    username: str
    real_name: Optional[str]
    employee_no: Optional[str]
    department: Optional[str]
    balance: int
    remaining_generations: int
    last_updated: Optional[datetime]


class UserCreditListResponse(BaseModel):
    """用户积分列表响应"""
    items: List[UserCreditItem]
    total: int
    page: int
    page_size: int


class CreditConfigItem(BaseModel):
    """积分配置项"""
    key: str
    value: str
    description: Optional[str]
    is_active: bool


class UpdateConfigRequest(BaseModel):
    """更新配置请求"""
    key: str = Field(..., description="配置键")
    value: str = Field(..., description="配置值")
    description: Optional[str] = Field(None, description="配置说明")


class OperationResponse(BaseModel):
    """操作响应"""
    success: bool
    message: str
    data: Optional[dict] = None


# ==================== 用户端API ====================

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


# ==================== 管理员API ====================

@router.get("/admin/users", response_model=UserCreditListResponse)
async def admin_get_all_users_credits(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索（用户名/姓名/工号）"),
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_active_superuser)
):
    """
    【管理员】获取所有用户积分列表
    """
    service = SolutionCreditService(db)
    users, total = service.get_all_users_credits(
        page=page,
        page_size=page_size,
        search=search
    )

    return UserCreditListResponse(
        items=[UserCreditItem(**u) for u in users],
        total=total,
        page=page,
        page_size=page_size
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
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
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


# ==================== 内部调用API ====================

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
