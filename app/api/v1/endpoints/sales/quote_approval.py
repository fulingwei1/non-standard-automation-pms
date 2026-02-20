# -*- coding: utf-8 -*-
"""
报价审批工作流 API

使用统一审批引擎实现报价审批流程。
报价在完成定价后需要提交审批以确认报价条款。
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.quote_approval import QuoteApprovalService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quotes/approval", tags=["报价审批工作流"])


# ==================== 请求模型 ====================


class QuoteSubmitApprovalRequest(BaseModel):
    """报价提交审批请求"""

    quote_ids: list[int] = Field(..., description="报价ID列表")
    version_ids: Optional[list[int]] = Field(None, description="指定版本ID列表（可选）")
    urgency: str = Field("NORMAL", description="紧急程度: LOW/NORMAL/HIGH/URGENT")
    comment: Optional[str] = Field(None, description="提交备注")


class ApprovalActionRequest(BaseModel):
    """审批操作请求"""

    task_id: int = Field(..., description="审批任务ID")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class BatchApprovalRequest(BaseModel):
    """批量审批请求"""

    task_ids: list[int] = Field(..., description="审批任务ID列表")
    action: str = Field(..., description="操作类型: approve/reject")
    comment: Optional[str] = Field(None, description="审批意见")


class WithdrawApprovalRequest(BaseModel):
    """撤回审批请求"""

    quote_id: int = Field(..., description="报价ID")
    reason: Optional[str] = Field(None, description="撤回原因")


# ==================== API 端点 ====================


@router.post("/submit", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def submit_for_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: QuoteSubmitApprovalRequest,
    current_user: User = Depends(security.require_permission("quote:create")),
) -> Any:
    """
    提交报价审批

    将已完成定价的报价提交到审批流程。
    适用于：
    - 新报价完成后提交审批
    - 被驳回的报价修改后重新提交
    - 报价版本更新后提交审批
    """
    service = QuoteApprovalService(db)
    result = service.submit_quotes_for_approval(
        quote_ids=request.quote_ids,
        initiator_id=current_user.id,
        version_ids=request.version_ids,
        urgency=request.urgency,
        comment=request.comment,
    )

    db.commit()

    return ResponseModel(
        code=200,
        message=f"提交完成: 成功 {len(result['success'])} 个, 失败 {len(result['errors'])} 个",
        data=result,
    )


@router.get("/pending", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_pending_approval_tasks(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    获取待审批的报价列表

    返回当前用户待审批的报价任务。
    """
    service = QuoteApprovalService(db)
    result = service.get_pending_tasks(
        user_id=current_user.id,
        customer_id=customer_id,
        offset=pagination.offset,
        limit=pagination.page_size,
    )

    return ResponseModel(
        code=200,
        message="获取待审批列表成功",
        data={
            "items": result["items"],
            "total": result["total"],
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (result["total"] + pagination.page_size - 1) // pagination.page_size,
        },
    )


@router.post("/action", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def perform_approval_action(
    *,
    db: Session = Depends(deps.get_db),
    request: ApprovalActionRequest,
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    执行审批操作

    对单个报价进行审批通过或驳回。
    """
    service = QuoteApprovalService(db)

    try:
        result = service.perform_action(
            task_id=request.task_id,
            action=request.action,
            approver_id=current_user.id,
            comment=request.comment,
        )

        db.commit()

        return ResponseModel(
            code=200,
            message="审批操作成功",
            data=result,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/batch-action", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def perform_batch_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: BatchApprovalRequest,
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    批量审批操作

    对多个报价进行批量审批通过或驳回。
    """
    service = QuoteApprovalService(db)
    result = service.perform_batch_actions(
        task_ids=request.task_ids,
        action=request.action,
        approver_id=current_user.id,
        comment=request.comment,
    )

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量审批完成: 成功 {len(result['success'])} 个, 失败 {len(result['errors'])} 个",
        data=result,
    )


@router.get(
    "/status/{quote_id}", response_model=ResponseModel, status_code=status.HTTP_200_OK
)
def get_approval_status(
    quote_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    查询报价审批状态

    获取指定报价的审批流程状态和历史。
    """
    service = QuoteApprovalService(db)
    result = service.get_quote_approval_status(quote_id)

    if result is None:
        raise HTTPException(status_code=404, detail="报价不存在")

    if result.get("approval_instance") is None:
        return ResponseModel(
            code=200,
            message="该报价暂无审批记录",
            data=result,
        )

    return ResponseModel(
        code=200,
        message="获取审批状态成功",
        data=result,
    )


@router.post("/withdraw", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def withdraw_approval(
    *,
    db: Session = Depends(deps.get_db),
    request: WithdrawApprovalRequest,
    current_user: User = Depends(security.require_permission("quote:create")),
) -> Any:
    """
    撤回审批

    撤回正在审批中的报价。
    """
    service = QuoteApprovalService(db)

    try:
        result = service.withdraw_approval(
            quote_id=request.quote_id,
            user_id=current_user.id,
            reason=request.reason,
        )

        db.commit()

        return ResponseModel(
            code=200,
            message="审批撤回成功",
            data=result,
        )
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_approval_history(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status_filter: Optional[str] = Query(None, description="状态筛选: APPROVED/REJECTED"),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    获取审批历史

    获取当前用户处理过的报价审批历史。
    """
    service = QuoteApprovalService(db)
    result = service.get_approval_history(
        user_id=current_user.id,
        status_filter=status_filter,
        offset=pagination.offset,
        limit=pagination.limit,
    )

    return ResponseModel(
        code=200,
        message="获取审批历史成功",
        data={
            "items": result["items"],
            "total": result["total"],
            "page": pagination.page,
            "page_size": pagination.page_size,
            "pages": (result["total"] + pagination.page_size - 1) // pagination.page_size,
        },
    )
