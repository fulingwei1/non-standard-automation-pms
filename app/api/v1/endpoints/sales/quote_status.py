# -*- coding: utf-8 -*-
"""
状态变更 - 自动生成
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
    prefix="/quotes/{quote_id}",
    tags=["status"]
)

# 共 3 个路由

# ==================== 状态变更 ====================


@router.put("/quotes/{quote_id}/submit", response_model=ResponseModel)
def submit_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交审批
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if not quote.current_version_id:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    quote.status = "PENDING_APPROVAL"
    db.commit()

    return ResponseModel(code=200, message="报价已提交审批")


@router.put("/quotes/{quote_id}/reject", response_model=ResponseModel)
def reject_quote(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    reason: Optional[str] = Query(None, description="驳回原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审批驳回
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    quote.status = "REJECTED"
    db.commit()

    return ResponseModel(code=200, message="报价已驳回")


@router.put("/quotes/{quote_id}/send", response_model=ResponseModel)
def send_quote_to_customer(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    send_method: Optional[str] = Query("EMAIL", description="发送方式：EMAIL/PRINT/OTHER"),
    send_to: Optional[str] = Query(None, description="发送对象（邮箱/联系人等）"),
    remark: Optional[str] = Query(None, description="发送备注"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    发送报价给客户
    只有已审批通过的报价才能发送给客户
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    if quote.status != QuoteStatusEnum.APPROVED:
        raise HTTPException(status_code=400, detail="只有已审批通过的报价才能发送给客户")

    # 更新报价状态为已发送（如果有SENT状态，否则保持APPROVED）
    # 这里简化处理，不改变状态，只记录发送操作

    # 可选：记录发送日志或通知

    return ResponseModel(
        code=200,
        message="报价已发送给客户",
        data={
            "quote_id": quote_id,
            "send_method": send_method,
            "send_to": send_to,
            "sent_at": datetime.now().isoformat()
        }
    )



