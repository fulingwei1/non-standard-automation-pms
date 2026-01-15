# -*- coding: utf-8 -*-
"""
成本分解 - 自动生成
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
    prefix="/quotes/{quote_id}/cost-breakdown",
    tags=["cost_breakdown"]
)

# 共 1 个路由

# ==================== 成本分解 ====================


@router.get("/quotes/{quote_id}/cost-breakdown", response_model=ResponseModel)
def get_quote_cost_breakdown(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价成本拆解
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()

    total_price = float(version.total_price or 0)
    total_cost = float(version.cost_total or 0)
    gross_margin = float(version.gross_margin or 0) if version.gross_margin else (total_price - total_cost) / total_price * 100 if total_price > 0 else 0

    cost_breakdown = []
    for item in items:
        item_price = float(item.qty or 0) * float(item.unit_price or 0)
        item_cost = float(item.cost or 0) * float(item.qty or 0)
        item_margin = (item_price - item_cost) / item_price * 100 if item_price > 0 else 0
        cost_breakdown.append({
            "item_name": item.item_name,
            "item_type": item.item_type,
            "qty": float(item.qty or 0),
            "unit_price": float(item.unit_price or 0),
            "total_price": item_price,
            "unit_cost": float(item.cost or 0),
            "total_cost": item_cost,
            "margin": round(item_margin, 2)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_price": total_price,
            "total_cost": total_cost,
            "gross_margin": round(gross_margin, 2),
            "breakdown": cost_breakdown
        }
    )



