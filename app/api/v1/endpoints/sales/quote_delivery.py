# -*- coding: utf-8 -*-
"""
交期验证 - 自动生成
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
    prefix="/quotes",
    tags=["delivery"]
)

# 共 1 个路由

# ==================== 交期验证 ====================


@router.get("/quotes/{quote_id}/delivery-validation", response_model=ResponseModel)
def validate_quote_delivery(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    交期校验API

    验证报价交期的合理性，包括：
    - 物料交期查询
    - 项目周期估算
    - 交期合理性分析
    - 优化建议
    """
    from app.services.delivery_validation_service import delivery_validation_service

    # 获取报价单
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取版本
    if version_id:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == version_id,
            QuoteVersion.quote_id == quote_id
        ).first()
    else:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.quote_id == quote_id,
            QuoteVersion.is_current == True
        ).first()

    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    # 获取报价明细
    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == version.id
    ).all()

    # 执行交期校验
    validation_result = delivery_validation_service.validate_delivery_date(
        db, quote, version, items
    )

    return ResponseModel(
        code=200,
        message="交期校验完成",
        data=validation_result
    )



