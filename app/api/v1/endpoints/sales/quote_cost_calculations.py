# -*- coding: utf-8 -*-
"""
成本计算 - 自动生成
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
    tags=["cost_calculations"]
)

# 共 2 个路由

# ==================== 成本计算与检查 ====================


@router.post("/quotes/{quote_id}/calculate-cost", response_model=ResponseModel)
def calculate_quote_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    自动计算报价成本
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

    total_cost = Decimal('0')
    total_price = Decimal(str(version.total_price or 0))

    for item in items:
        item_cost = Decimal(str(item.cost or 0)) * Decimal(str(item.qty or 0))
        total_cost += item_cost

    # 更新版本成本
    version.cost_total = float(total_cost)

    # 计算毛利率
    if total_price > 0:
        gross_margin = ((total_price - total_cost) / total_price * 100)
        version.gross_margin = float(gross_margin)
    else:
        version.gross_margin = None

    db.commit()
    db.refresh(version)

    return ResponseModel(
        code=200,
        message="成本计算完成",
        data={
            "total_price": float(total_price),
            "total_cost": float(total_cost),
            "gross_margin": float(version.gross_margin) if version.gross_margin else None
        }
    )


@router.get("/quotes/{quote_id}/cost-check", response_model=CostCheckResponse)
def check_quote_cost(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="报价版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本完整性检查
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

    checks = []

    # 检查1：是否有成本明细
    if not items:
        checks.append({
            "check_item": "成本明细",
            "status": "FAIL",
            "message": "未添加任何成本明细"
        })
    else:
        checks.append({
            "check_item": "成本明细",
            "status": "PASS",
            "message": f"已添加{len(items)}项成本明细"
        })

    # 检查2：成本项是否完整
    incomplete_items = []
    for item in items:
        if not item.cost or item.cost == 0:
            incomplete_items.append(item.item_name or f"项目{item.id}")

    if incomplete_items:
        checks.append({
            "check_item": "成本项完整性",
            "status": "FAIL",
            "message": f"以下成本项未填写成本：{', '.join(incomplete_items[:5])}{'...' if len(incomplete_items) > 5 else ''}"
        })
    else:
        checks.append({
            "check_item": "成本项完整性",
            "status": "PASS",
            "message": "所有成本项已填写"
        })

    # 检查3：毛利率检查
    margin_threshold = Decimal('20.0')  # 默认阈值20%
    current_margin = version.gross_margin or 0

    if current_margin < margin_threshold:
        checks.append({
            "check_item": "毛利率检查",
            "status": "WARNING" if current_margin >= 15 else "FAIL",
            "message": f"毛利率{current_margin:.2f}%，低于阈值{margin_threshold}%",
            "current_margin": float(current_margin),
            "threshold": float(margin_threshold)
        })
    else:
        checks.append({
            "check_item": "毛利率检查",
            "status": "PASS",
            "message": f"毛利率{current_margin:.2f}%，符合要求"
        })

    # 检查4：交期检查
    items_without_leadtime = []
    for item in items:
        if not item.lead_time_days and item.item_type in ['硬件', '外购件', '标准件']:
            items_without_leadtime.append(item.item_name or f"项目{item.id}")

    if items_without_leadtime:
        checks.append({
            "check_item": "交期校验",
            "status": "WARNING",
            "message": f"以下关键物料未填写交期：{', '.join(items_without_leadtime[:5])}{'...' if len(items_without_leadtime) > 5 else ''}"
        })
    else:
        checks.append({
            "check_item": "交期校验",
            "status": "PASS",
            "message": "关键物料交期已填写"
        })

    is_complete = all(check["status"] == "PASS" for check in checks)

    return CostCheckResponse(
        is_complete=is_complete,
        checks=checks,
        total_price=Decimal(str(version.total_price or 0)),
        total_cost=Decimal(str(version.cost_total or 0)),
        gross_margin=Decimal(str(current_margin))
    )



