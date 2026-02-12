# -*- coding: utf-8 -*-
"""
报价成本计算
包含：成本计算、毛利计算、价格建议
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion, QuoteItem
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


def calculate_margin(price: Decimal, cost: Decimal) -> Decimal:
    """计算毛利率"""
    if price and price > 0:
        return ((price - cost) / price * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Decimal('0')


def calculate_markup(price: Decimal, cost: Decimal) -> Decimal:
    """计算加价率"""
    if cost and cost > 0:
        return ((price - cost) / cost * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return Decimal('0')


@router.get("/quotes/{quote_id}/cost-calculations", response_model=ResponseModel)
def get_cost_calculations(
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价成本计算结果

    Args:
        quote_id: 报价ID
        version_id: 版本ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 成本计算结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    vid = version_id or quote.current_version_id
    if not vid:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == vid).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == vid).all()

    # 计算各项
    total_cost = Decimal('0')
    total_price = Decimal('0')
    item_details = []

    for item in items:
        item_cost = item.cost or Decimal('0')
        item_qty = item.qty or Decimal('0')
        item_unit_price = item.unit_price or Decimal('0')
        item_amount = item_qty * item_unit_price

        total_cost += item_cost
        total_price += item_amount

        item_margin = calculate_margin(item_amount, item_cost)
        item_markup = calculate_markup(item_amount, item_cost)

        item_details.append({
            "id": item.id,
            "item_name": item.item_name,
            "qty": float(item_qty),
            "unit_price": float(item_unit_price),
            "amount": float(item_amount),
            "cost": float(item_cost),
            "profit": float(item_amount - item_cost),
            "margin_rate": float(item_margin),
            "markup_rate": float(item_markup),
        })

    # 总体计算
    gross_profit = total_price - total_cost
    margin_rate = calculate_margin(total_price, total_cost)
    markup_rate = calculate_markup(total_price, total_cost)

    return ResponseModel(
        code=200,
        message="获取成本计算成功",
        data={
            "quote_id": quote_id,
            "version_id": vid,
            "summary": {
                "total_price": float(total_price),
                "total_cost": float(total_cost),
                "gross_profit": float(gross_profit),
                "margin_rate": float(margin_rate),
                "markup_rate": float(markup_rate),
            },
            "items": item_details
        }
    )


@router.post("/quotes/cost-calculations/simulate", response_model=ResponseModel)
def simulate_cost(
    simulation_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    模拟成本计算

    Args:
        simulation_data: 模拟数据（items: [{cost, price, qty}]）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 模拟结果
    """
    items = simulation_data.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="请提供明细项")

    total_cost = Decimal('0')
    total_price = Decimal('0')
    results = []

    for item in items:
        cost = Decimal(str(item.get("cost", 0)))
        price = Decimal(str(item.get("price", 0)))
        qty = Decimal(str(item.get("qty", 1)))

        item_amount = price * qty
        item_cost = cost * qty

        total_cost += item_cost
        total_price += item_amount

        results.append({
            "cost": float(cost),
            "price": float(price),
            "qty": float(qty),
            "amount": float(item_amount),
            "total_cost": float(item_cost),
            "profit": float(item_amount - item_cost),
            "margin_rate": float(calculate_margin(item_amount, item_cost)),
        })

    gross_profit = total_price - total_cost
    margin_rate = calculate_margin(total_price, total_cost)

    return ResponseModel(
        code=200,
        message="模拟计算完成",
        data={
            "summary": {
                "total_price": float(total_price),
                "total_cost": float(total_cost),
                "gross_profit": float(gross_profit),
                "margin_rate": float(margin_rate),
            },
            "items": results
        }
    )


@router.post("/quotes/cost-calculations/price-suggestion", response_model=ResponseModel)
def get_price_suggestion(
    suggestion_data: dict,
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取价格建议（根据目标毛利率）

    Args:
        suggestion_data: 建议数据（cost: 成本, target_margin: 目标毛利率）
        current_user: 当前用户

    Returns:
        ResponseModel: 价格建议
    """
    cost = Decimal(str(suggestion_data.get("cost", 0)))
    target_margin = Decimal(str(suggestion_data.get("target_margin", 20)))

    if cost <= 0:
        raise HTTPException(status_code=400, detail="成本必须大于0")

    if target_margin >= 100:
        raise HTTPException(status_code=400, detail="目标毛利率必须小于100%")

    # 根据毛利率公式: margin = (price - cost) / price
    # 推导: price = cost / (1 - margin/100)
    suggested_price = (cost / (1 - target_margin / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # 提供多档建议
    suggestions = []
    for margin in [15, 20, 25, 30, 35]:
        m = Decimal(str(margin))
        price = (cost / (1 - m / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        profit = price - cost
        suggestions.append({
            "margin_rate": margin,
            "suggested_price": float(price),
            "expected_profit": float(profit),
        })

    return ResponseModel(
        code=200,
        message="获取价格建议成功",
        data={
            "cost": float(cost),
            "target_margin": float(target_margin),
            "suggested_price": float(suggested_price),
            "expected_profit": float(suggested_price - cost),
            "suggestions": suggestions
        }
    )


@router.post("/quotes/{quote_id}/cost-calculations/batch-update", response_model=ResponseModel)
def batch_update_prices(
    quote_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    批量更新价格（按统一加价率或毛利率）

    Args:
        quote_id: 报价ID
        update_data: 更新数据（mode: markup/margin, rate: 比率, version_id）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version_id = update_data.get("version_id") or quote.current_version_id
    if not version_id:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    mode = update_data.get("mode", "markup")  # markup or margin
    rate = Decimal(str(update_data.get("rate", 20)))

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version_id).all()

    updated_count = 0
    for item in items:
        if item.cost and item.cost > 0:
            if mode == "markup":
                # 加价率: price = cost * (1 + rate/100)
                new_price = (item.cost * (1 + rate / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                # 毛利率: price = cost / (1 - rate/100)
                if rate >= 100:
                    continue
                new_price = (item.cost / (1 - rate / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

            item.unit_price = new_price
            updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"已更新 {updated_count} 个明细项的价格",
        data={"updated_count": updated_count, "mode": mode, "rate": float(rate)}
    )


@router.get("/quotes/cost-calculations/margin-analysis", response_model=ResponseModel)
def get_margin_analysis(
    min_margin: float = Query(0, description="最小毛利率"),
    max_margin: float = Query(100, description="最大毛利率"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取毛利率分析

    Args:
        min_margin: 最小毛利率
        max_margin: 最大毛利率
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 分析结果
    """
    versions = db.query(QuoteVersion).filter(
        QuoteVersion.gross_margin is not None,
        QuoteVersion.gross_margin >= min_margin,
        QuoteVersion.gross_margin <= max_margin
    ).all()

    if not versions:
        return ResponseModel(
            code=200,
            message="无数据",
            data={"count": 0, "avg_margin": 0, "distribution": []}
        )

    margins = [float(v.gross_margin) for v in versions if v.gross_margin]
    avg_margin = sum(margins) / len(margins) if margins else 0

    # 分布统计
    distribution = {
        "0-10%": 0,
        "10-15%": 0,
        "15-20%": 0,
        "20-25%": 0,
        "25-30%": 0,
        "30%+": 0,
    }

    for m in margins:
        if m < 10:
            distribution["0-10%"] += 1
        elif m < 15:
            distribution["10-15%"] += 1
        elif m < 20:
            distribution["15-20%"] += 1
        elif m < 25:
            distribution["20-25%"] += 1
        elif m < 30:
            distribution["25-30%"] += 1
        else:
            distribution["30%+"] += 1

    return ResponseModel(
        code=200,
        message="获取毛利分析成功",
        data={
            "count": len(margins),
            "avg_margin": round(avg_margin, 2),
            "min_margin": round(min(margins), 2) if margins else 0,
            "max_margin": round(max(margins), 2) if margins else 0,
            "distribution": [{"range": k, "count": v} for k, v in distribution.items()]
        }
    )
