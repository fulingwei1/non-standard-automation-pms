# -*- coding: utf-8 -*-
"""
报价单据级审批便捷 API

提供以单个报价为中心的审批操作端点：
- POST /quotes/{quote_id}/submit  — 提交单个报价审批
- GET  /quotes/{quote_id}/approvals — 查询审批进度
- POST /quotes/{quote_id}/approve  — 审批通过
- POST /quotes/{quote_id}/reject   — 审批驳回
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.quote_approval import QuoteApprovalService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["报价审批便捷操作"])


# ==================== 请求模型 ====================


class QuoteSubmitRequest(BaseModel):
    """单报价提交审批请求"""

    urgency: str = Field("NORMAL", description="紧急程度: LOW/NORMAL/HIGH/URGENT")
    comment: Optional[str] = Field(None, description="提交备注")


class QuoteApproveRejectRequest(BaseModel):
    """审批通过/驳回请求"""

    comment: Optional[str] = Field(None, description="审批意见")


# ==================== API 端点 ====================


@router.post(
    "/quotes/{quote_id}/submit",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def submit_quote_for_approval(
    quote_id: int,
    *,
    db: Session = Depends(deps.get_db),
    request: QuoteSubmitRequest = QuoteSubmitRequest(),
    current_user: User = Depends(security.require_permission("quote:create")),
) -> Any:
    """
    提交单个报价审批

    将指定报价提交到审批流程。报价状态须为 DRAFT 或 REJECTED。
    """
    service = QuoteApprovalService(db)
    result = service.submit_quotes_for_approval(
        quote_ids=[quote_id],
        initiator_id=current_user.id,
        urgency=request.urgency,
        comment=request.comment,
    )

    db.commit()

    if result.get("errors"):
        error = result["errors"][0]
        raise HTTPException(status_code=400, detail=error.get("error", "提交失败"))

    logger.info(f"报价 {quote_id} 已提交审批, 操作人: {current_user.id}")

    return ResponseModel(
        code=200,
        message="报价已提交审批",
        data={"quote_id": quote_id, "result": result.get("success", [])},
    )


@router.get(
    "/quotes/{quote_id}/approvals",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def get_quote_approvals(
    quote_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("quote:read")),
) -> Any:
    """
    查询报价审批进度

    获取指定报价的审批流程状态和审批记录。
    """
    service = QuoteApprovalService(db)
    result = service.get_quote_approval_status(quote_id)

    if result is None:
        raise HTTPException(status_code=404, detail="报价不存在")

    return ResponseModel(
        code=200,
        message="获取审批进度成功",
        data=result,
    )


@router.post(
    "/quotes/{quote_id}/approve",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def approve_quote(
    quote_id: int,
    *,
    db: Session = Depends(deps.get_db),
    request: QuoteApproveRejectRequest = QuoteApproveRejectRequest(),
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    审批通过报价

    查找当前用户在该报价上的待处理审批任务并执行通过操作。
    """
    service = QuoteApprovalService(db)

    # 查找该报价关联的当前用户待处理的审批任务
    pending = service.get_pending_tasks(user_id=current_user.id, offset=0, limit=100)
    task_id = _find_task_for_quote(pending, quote_id)

    if not task_id:
        raise HTTPException(status_code=404, detail="未找到该报价的待审批任务")

    try:
        result = service.perform_action(
            task_id=task_id,
            action="approve",
            approver_id=current_user.id,
            comment=request.comment,
        )
        db.commit()

        logger.info(f"报价 {quote_id} 审批通过, 操作人: {current_user.id}")

        return ResponseModel(
            code=200,
            message="报价审批通过",
            data={"quote_id": quote_id, "task_id": task_id},
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/quotes/{quote_id}/reject",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def reject_quote(
    quote_id: int,
    *,
    db: Session = Depends(deps.get_db),
    request: QuoteApproveRejectRequest,
    current_user: User = Depends(security.require_permission("quote:approve")),
) -> Any:
    """
    审批驳回报价

    查找当前用户在该报价上的待处理审批任务并执行驳回操作。
    """
    service = QuoteApprovalService(db)

    pending = service.get_pending_tasks(user_id=current_user.id, offset=0, limit=100)
    task_id = _find_task_for_quote(pending, quote_id)

    if not task_id:
        raise HTTPException(status_code=404, detail="未找到该报价的待审批任务")

    try:
        result = service.perform_action(
            task_id=task_id,
            action="reject",
            approver_id=current_user.id,
            comment=request.comment,
        )
        db.commit()

        logger.info(f"报价 {quote_id} 审批驳回, 操作人: {current_user.id}")

        return ResponseModel(
            code=200,
            message="报价已驳回",
            data={"quote_id": quote_id, "task_id": task_id},
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


def _find_task_for_quote(pending_result: dict, quote_id: int) -> Optional[int]:
    """从待审批列表中查找指定报价的任务ID"""
    items = pending_result.get("items", [])
    for item in items:
        entity_id = item.get("entity_id") or item.get("quote_id")
        if entity_id == quote_id:
            return item.get("task_id") or item.get("id")
    return None
