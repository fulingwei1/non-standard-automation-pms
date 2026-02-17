# -*- coding: utf-8 -*-
"""
报价成本明细管理
包含：成本分类明细、成本项管理
"""

from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion, QuoteItem
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/quotes/{quote_id}/cost-breakdown", response_model=ResponseModel)
def get_cost_breakdown(
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，默认当前版本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价成本明细分解

    Args:
        quote_id: 报价ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 成本明细
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    vid = version_id or quote.current_version_id
    if not vid:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    version = get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == vid
    ).order_by(QuoteItem.id).all()

    # 按类型分组汇总
    categories = {}
    total_cost = Decimal('0')
    total_price = Decimal('0')

    for item in items:
        cat = item.cost_category or item.item_type or "其他"
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "items": [],
                "subtotal_cost": Decimal('0'),
                "subtotal_price": Decimal('0'),
            }

        item_cost = item.cost or Decimal('0')
        item_price = (item.qty or Decimal('0')) * (item.unit_price or Decimal('0'))

        categories[cat]["items"].append({
            "id": item.id,
            "item_name": item.item_name,
            "specification": item.specification,
            "qty": float(item.qty) if item.qty else 0,
            "unit": item.unit,
            "unit_price": float(item.unit_price) if item.unit_price else 0,
            "cost": float(item_cost),
            "cost_source": item.cost_source,
        })
        categories[cat]["subtotal_cost"] += item_cost
        categories[cat]["subtotal_price"] += item_price
        total_cost += item_cost
        total_price += item_price

    # 转换为列表并计算占比
    breakdown = []
    for cat_data in categories.values():
        cat_data["subtotal_cost"] = float(cat_data["subtotal_cost"])
        cat_data["subtotal_price"] = float(cat_data["subtotal_price"])
        cat_data["cost_ratio"] = round(cat_data["subtotal_cost"] / float(total_cost) * 100, 2) if total_cost else 0
        breakdown.append(cat_data)

    return ResponseModel(
        code=200,
        message="获取成本明细成功",
        data={
            "quote_id": quote_id,
            "version_id": vid,
            "total_cost": float(total_cost),
            "total_price": float(total_price),
            "gross_margin": round((float(total_price) - float(total_cost)) / float(total_price) * 100, 2) if total_price else 0,
            "breakdown": breakdown
        }
    )


@router.put("/quotes/cost-breakdown/items/{item_id}", response_model=ResponseModel)
def update_cost_item(
    item_id: int,
    item_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新成本明细项

    Args:
        item_id: 明细项ID
        item_data: 更新数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    item = get_or_404(db, QuoteItem, item_id, detail="明细项不存在")

    # 可更新字段
    updatable = ["cost", "cost_category", "cost_source", "unit_price", "qty", "remark"]
    for field in updatable:
        if field in item_data:
            setattr(item, field, item_data[field])

    db.commit()

    return ResponseModel(code=200, message="成本明细更新成功", data={"id": item.id})


@router.post("/quotes/{quote_id}/cost-breakdown/recalculate", response_model=ResponseModel)
def recalculate_cost(
    quote_id: int,
    version_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    重新计算报价成本汇总

    Args:
        quote_id: 报价ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 计算结果
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")

    vid = version_id or quote.current_version_id
    version = get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == vid).all()

    total_cost = Decimal('0')
    total_price = Decimal('0')

    for item in items:
        total_cost += item.cost or Decimal('0')
        if item.qty and item.unit_price:
            total_price += item.qty * item.unit_price

    # 更新版本汇总
    version.cost_total = total_cost
    version.total_price = total_price
    if total_price > 0:
        version.gross_margin = ((total_price - total_cost) / total_price * 100).quantize(Decimal('0.01'))
        version.margin_warning = version.gross_margin < 15
    else:
        version.gross_margin = Decimal('0')

    version.cost_breakdown_complete = True
    db.commit()

    return ResponseModel(
        code=200,
        message="成本重新计算完成",
        data={
            "version_id": vid,
            "total_cost": float(total_cost),
            "total_price": float(total_price),
            "gross_margin": float(version.gross_margin)
        }
    )
