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
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Quote
from app.models.sales.operation_log import SalesOperationType
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.quote_approval import QuoteApprovalService
from app.services.sales.quote_operation_audit import (
    log_quote_operation,
    log_quote_version_operation,
    quote_audit_value,
    quote_version_audit_value,
)

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
    remark: Optional[str] = Field(None, description="兼容旧字段：审批意见")


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

    if result.get("errors"):
        error = result["errors"][0]
        message = error.get("error", "提交失败")
        status_code = status.HTTP_404_NOT_FOUND if message == "报价不存在" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message)

    db.commit()

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
        quote = db.query(Quote).filter(Quote.id == quote_id).first()
        if not quote:
            raise HTTPException(status_code=404, detail="报价不存在")
        if not _can_direct_approve_funnel_quote(quote):
            raise HTTPException(status_code=404, detail="未找到该报价的待审批任务")
        return _approve_quote_directly(
            db=db,
            quote=quote,
            approver=current_user,
            comment=request.comment or request.remark,
        )

    try:
        service.perform_action(
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
        service.perform_action(
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


def _approve_quote_directly(
    *,
    db: Session,
    quote: Quote,
    approver: User,
    comment: Optional[str] = None,
) -> ResponseModel:
    """无待办任务时的单据级便捷审批兜底。"""
    old_quote_value = quote_audit_value(quote)
    version = quote.current_version
    old_version_value = quote_version_audit_value(version) if version else None

    quote.status = "APPROVED"
    if version:
        version.approved_by = approver.id
        version.approved_at = datetime.now()
    log_quote_operation(
        db,
        quote,
        SalesOperationType.APPROVE,
        approver,
        old_value=old_quote_value,
        new_value=quote_audit_value(quote),
        operation_desc="报价审批通过",
        remark=comment,
    )
    if version and old_version_value:
        log_quote_version_operation(
            db,
            version,
            SalesOperationType.APPROVE,
            approver,
            old_value=old_version_value,
            new_value=quote_version_audit_value(version),
            operation_desc="报价版本审批通过",
            remark=comment,
        )
    db.commit()

    logger.info("报价 %s 已直接审批通过, 操作人: %s", quote.id, approver.id)

    return ResponseModel(
        code=200,
        message="报价审批通过",
        data={
            "quote_id": quote.id,
            "task_id": None,
            "direct_approval": True,
            "comment": comment,
        },
    )


def _can_direct_approve_funnel_quote(quote: Quote) -> bool:
    """仅允许漏斗 G2 自动生成的报价使用无任务便捷审批兜底。"""
    return bool(
        quote.quote_code
        and quote.quote_code.startswith("QT")
        and quote.status in {"DRAFT", "REJECTED", "SUBMITTED", "PENDING_APPROVAL"}
    )
