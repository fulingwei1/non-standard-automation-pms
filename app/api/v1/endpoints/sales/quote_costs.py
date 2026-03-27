# -*- coding: utf-8 -*-
"""
报价成本管理（合并自 quote_cost_analysis / quote_cost_breakdown / quote_cost_calculations）

功能：
- 报价成本分析（物料/人工/费用明细、版本趋势、基准对比）
- 成本拆解（分部分项明细、分类汇总）
- 成本计算（自动计算总价/毛利/毛利率、模拟计算、价格建议、批量更新）
"""

import logging
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.core.sales_permissions import check_sales_data_permission, filter_sales_data_by_scope
from app.models.sales import Quote, QuoteItem, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404
from app.utils.json_helpers import safe_json_loads

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 通用工具函数 ====================


def _check_quote_scope(quote: Quote, current_user: User, db: Session) -> None:
    """校验当前用户是否有权访问该报价，无权则抛 403"""
    if not check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该报价的成本数据")


def _to_decimal(value) -> Decimal:
    """安全转换为 Decimal，失败返回 0"""
    if value in (None, ""):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning(f"成本字段转换失败: value={value!r}, error={e}")
        return Decimal("0")


def _split_remark_meta(remark: Optional[str]) -> tuple[str, dict]:
    """
    解析备注中的技术元数据

    Args:
        remark: 备注字符串，可能包含 [tech-meta] 标记

    Returns:
        (清理后的备注, 技术元数据字典)
    """
    if not remark:
        return "", {}
    if "[tech-meta]" not in remark:
        return remark, {}

    base, raw_meta = remark.split("[tech-meta]", 1)
    tech_meta = safe_json_loads(
        raw_meta,
        default={},
        field_name="tech_meta",
        log_error=False,
    )
    return base.strip(), tech_meta


def _item_cost_from_meta(item: QuoteItem, tech_meta: dict) -> Decimal:
    total_cost = _to_decimal(tech_meta.get("total_cost"))
    if total_cost > 0:
        return total_cost

    parts = _to_decimal(tech_meta.get("material_cost")) + _to_decimal(tech_meta.get("labor_cost")) + _to_decimal(tech_meta.get("overhead_cost"))
    if parts > 0:
        return parts

    return _to_decimal(item.cost)


def calculate_margin(price: Decimal, cost: Decimal) -> Decimal:
    """计算毛利率"""
    if price and price > 0:
        return ((price - cost) / price * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal("0")


def calculate_markup(price: Decimal, cost: Decimal) -> Decimal:
    """计算加价率"""
    if cost and cost > 0:
        return ((price - cost) / cost * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Decimal("0")


# ==================== 成本分析 ====================


@router.get("/quotes/{quote_id}/cost-analysis", response_model=ResponseModel)
def get_cost_analysis(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价成本分析

    Args:
        quote_id: 报价ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 成本分析结果
    """
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")
    if not check_sales_data_permission(quote, current_user, db, "owner_id"):
        raise HTTPException(status_code=403, detail="无权访问该报价的成本分析")

    versions = (
        db.query(QuoteVersion)
        .filter(QuoteVersion.quote_id == quote_id)
        .order_by(QuoteVersion.created_at)
        .all()
    )

    if not versions:
        return ResponseModel(code=200, message="暂无版本数据", data={})

    # 版本趋势
    version_trend = [
        {
            "version_no": v.version_no,
            "total_price": float(v.total_price) if v.total_price else 0,
            "cost_total": float(v.cost_total) if v.cost_total else 0,
            "gross_margin": float(v.gross_margin) if v.gross_margin else 0,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]

    # 当前版本的成本结构
    current = versions[-1]
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == current.id).all()

    # 按类型汇总
    cost_by_type = {}
    for item in items:
        t = item.item_type or "其他"
        if t not in cost_by_type:
            cost_by_type[t] = Decimal("0")
        cost_by_type[t] += item.cost or Decimal("0")

    cost_structure = [
        {
            "type": k,
            "cost": float(v),
            "ratio": (
                round(float(v) / float(current.cost_total) * 100, 2) if current.cost_total else 0
            ),
        }
        for k, v in cost_by_type.items()
    ]

    # 计算版本间变化
    changes = []
    for i in range(1, len(versions)):
        prev = versions[i - 1]
        curr = versions[i]
        price_change = float(curr.total_price or 0) - float(prev.total_price or 0)
        cost_change = float(curr.cost_total or 0) - float(prev.cost_total or 0)
        margin_change = float(curr.gross_margin or 0) - float(prev.gross_margin or 0)

        changes.append(
            {
                "from_version": prev.version_no,
                "to_version": curr.version_no,
                "price_change": price_change,
                "cost_change": cost_change,
                "margin_change": round(margin_change, 2),
            }
        )

    return ResponseModel(
        code=200,
        message="获取成本分析成功",
        data={
            "quote_id": quote_id,
            "version_count": len(versions),
            "current_version": {
                "version_no": current.version_no,
                "total_price": float(current.total_price) if current.total_price else 0,
                "cost_total": float(current.cost_total) if current.cost_total else 0,
                "gross_margin": float(current.gross_margin) if current.gross_margin else 0,
            },
            "cost_structure": cost_structure,
            "version_trend": version_trend,
            "version_changes": changes,
        },
    )


@router.get("/quotes/cost-analysis/benchmark", response_model=ResponseModel)
def get_cost_benchmark(
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取成本基准对比（同类报价的平均毛利率等）

    Args:
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 基准数据
    """
    ninety_days_ago = date.today() - timedelta(days=90)

    base_query = filter_sales_data_by_scope(
        db.query(Quote), current_user, db, Quote, "owner_id"
    ).filter(Quote.created_at >= ninety_days_ago)

    from sqlalchemy import select

    scoped_ids = base_query.with_entities(Quote.id).subquery()

    result = (
        db.query(
            func.count(Quote.id).label("quote_count"),
            func.avg(QuoteVersion.gross_margin).label("avg_margin"),
            func.min(QuoteVersion.gross_margin).label("min_margin"),
            func.max(QuoteVersion.gross_margin).label("max_margin"),
        )
        .join(QuoteVersion, Quote.current_version_id == QuoteVersion.id)
        .filter(Quote.id.in_(select(scoped_ids.c.id)))
        .first()
    )

    from sqlalchemy import case as sa_case

    margin_range = sa_case(
        (QuoteVersion.gross_margin < 10, "0-10%"),
        (QuoteVersion.gross_margin < 20, "10-20%"),
        (QuoteVersion.gross_margin < 30, "20-30%"),
        else_="30%+",
    ).label("range")
    distribution = (
        db.query(margin_range, func.count(Quote.id).label("count"))
        .join(QuoteVersion, Quote.current_version_id == QuoteVersion.id)
        .filter(Quote.id.in_(select(scoped_ids.c.id)))
        .group_by(margin_range)
        .all()
    )

    return ResponseModel(
        code=200,
        message="获取成本基准成功",
        data={
            "period": "近90天",
            "quote_count": result.quote_count if result else 0,
            "avg_margin": round(float(result.avg_margin), 2) if result and result.avg_margin else 0,
            "min_margin": round(float(result.min_margin), 2) if result and result.min_margin else 0,
            "max_margin": round(float(result.max_margin), 2) if result and result.max_margin else 0,
            "margin_distribution": [{"range": d.range, "count": d.count} for d in distribution],
        },
    )


# ==================== 成本拆解 ====================


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
    _check_quote_scope(quote, current_user, db)

    vid = version_id or quote.current_version_id
    if not vid:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == vid
    ).order_by(QuoteItem.id).all()

    # 按类型分组汇总
    categories = {}
    total_cost = Decimal('0')
    total_price = Decimal('0')
    total_material_cost = Decimal('0')
    total_labor_cost = Decimal('0')
    total_overhead_cost = Decimal('0')

    for item in items:
        cat = item.cost_category or item.item_type or "其他"
        if cat not in categories:
            categories[cat] = {
                "category": cat,
                "items": [],
                "subtotal_cost": Decimal('0'),
                "subtotal_price": Decimal('0'),
            }

        clean_remark, tech_meta = _split_remark_meta(item.remark)
        item_cost = _item_cost_from_meta(item, tech_meta)
        item_price = (item.qty or Decimal('0')) * (item.unit_price or Decimal('0'))

        material_cost = _to_decimal(tech_meta.get("material_cost"))
        labor_cost = _to_decimal(tech_meta.get("labor_cost"))
        overhead_cost = _to_decimal(tech_meta.get("overhead_cost"))

        categories[cat]["items"].append({
            "id": item.id,
            "item_name": item.item_name,
            "specification": item.specification,
            "qty": float(item.qty) if item.qty else 0,
            "unit": item.unit,
            "unit_price": float(item.unit_price) if item.unit_price else 0,
            "cost": float(item_cost),
            "cost_source": item.cost_source,
            "remark": clean_remark,
            **tech_meta,
        })
        categories[cat]["subtotal_cost"] += item_cost
        categories[cat]["subtotal_price"] += item_price
        total_cost += item_cost
        total_price += item_price

        total_material_cost += material_cost
        total_labor_cost += labor_cost
        total_overhead_cost += overhead_cost

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
            "cost_structure": {
                "material_cost": float(total_material_cost),
                "labor_cost": float(total_labor_cost),
                "overhead_cost": float(total_overhead_cost),
                "other_cost": float(max(Decimal('0'), total_cost - total_material_cost - total_labor_cost - total_overhead_cost)),
            },
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

    # 数据权限：通过明细项的版本 -> 报价链路校验
    version = db.query(QuoteVersion).filter(QuoteVersion.id == item.quote_version_id).first()
    if version:
        quote = db.query(Quote).filter(Quote.id == version.quote_id).first()
        if quote:
            _check_quote_scope(quote, current_user, db)

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
    _check_quote_scope(quote, current_user, db)

    vid = version_id or quote.current_version_id
    version = get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == vid).all()

    total_cost = Decimal('0')
    total_price = Decimal('0')

    for item in items:
        _, tech_meta = _split_remark_meta(item.remark)
        item_cost = _item_cost_from_meta(item, tech_meta)
        item.cost = item_cost

        total_cost += item_cost
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


@router.post("/quotes/{quote_id}/recalculate", response_model=ResponseModel)
def recalculate_quote_cost(
    quote_id: int,
    version_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """兼容入口：按周计划暴露 /quotes/{id}/recalculate。"""
    return recalculate_cost(
        quote_id=quote_id,
        version_id=version_id,
        db=db,
        current_user=current_user,
    )


# ==================== 成本计算 ====================


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
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")
    _check_quote_scope(quote, current_user, db)

    vid = version_id or quote.current_version_id
    if not vid:
        raise HTTPException(status_code=400, detail="请指定报价版本")

    get_or_404(db, QuoteVersion, vid, detail="版本不存在")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == vid).all()

    # 计算各项
    total_cost = Decimal("0")
    total_price = Decimal("0")
    item_details = []

    for item in items:
        item_cost = item.cost or Decimal("0")
        item_qty = item.qty or Decimal("0")
        item_unit_price = item.unit_price or Decimal("0")
        item_amount = item_qty * item_unit_price

        total_cost += item_cost
        total_price += item_amount

        item_margin = calculate_margin(item_amount, item_cost)
        item_markup = calculate_markup(item_amount, item_cost)

        item_details.append(
            {
                "id": item.id,
                "item_name": item.item_name,
                "qty": float(item_qty),
                "unit_price": float(item_unit_price),
                "amount": float(item_amount),
                "cost": float(item_cost),
                "profit": float(item_amount - item_cost),
                "margin_rate": float(item_margin),
                "markup_rate": float(item_markup),
            }
        )

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
            "items": item_details,
        },
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

    total_cost = Decimal("0")
    total_price = Decimal("0")
    results = []

    for item in items:
        cost = Decimal(str(item.get("cost", 0)))
        price = Decimal(str(item.get("price", 0)))
        qty = Decimal(str(item.get("qty", 1)))

        item_amount = price * qty
        item_cost = cost * qty

        total_cost += item_cost
        total_price += item_amount

        results.append(
            {
                "cost": float(cost),
                "price": float(price),
                "qty": float(qty),
                "amount": float(item_amount),
                "total_cost": float(item_cost),
                "profit": float(item_amount - item_cost),
                "margin_rate": float(calculate_margin(item_amount, item_cost)),
            }
        )

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
            "items": results,
        },
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
    suggested_price = (cost / (1 - target_margin / 100)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    # 提供多档建议
    suggestions = []
    for margin in [15, 20, 25, 30, 35]:
        m = Decimal(str(margin))
        price = (cost / (1 - m / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        profit = price - cost
        suggestions.append(
            {
                "margin_rate": margin,
                "suggested_price": float(price),
                "expected_profit": float(profit),
            }
        )

    return ResponseModel(
        code=200,
        message="获取价格建议成功",
        data={
            "cost": float(cost),
            "target_margin": float(target_margin),
            "suggested_price": float(suggested_price),
            "expected_profit": float(suggested_price - cost),
            "suggestions": suggestions,
        },
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
    quote = get_or_404(db, Quote, quote_id, detail="报价不存在")
    _check_quote_scope(quote, current_user, db)

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
                new_price = (item.cost * (1 + rate / 100)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
            else:
                # 毛利率: price = cost / (1 - rate/100)
                if rate >= 100:
                    continue
                new_price = (item.cost / (1 - rate / 100)).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )

            item.unit_price = new_price
            updated_count += 1

    db.commit()

    return ResponseModel(
        code=200,
        message=f"已更新 {updated_count} 个明细项的价格",
        data={"updated_count": updated_count, "mode": mode, "rate": float(rate)},
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
    scoped_quotes = filter_sales_data_by_scope(
        db.query(Quote), current_user, db, Quote, "owner_id"
    )
    scoped_quote_ids = [q.id for q in scoped_quotes.with_entities(Quote.id).all()]

    versions = (
        db.query(QuoteVersion)
        .filter(
            QuoteVersion.quote_id.in_(scoped_quote_ids) if scoped_quote_ids else False,
            QuoteVersion.gross_margin is not None,
            QuoteVersion.gross_margin >= min_margin,
            QuoteVersion.gross_margin <= max_margin,
        )
        .all()
    )

    if not versions:
        return ResponseModel(
            code=200, message="无数据", data={"count": 0, "avg_margin": 0, "distribution": []}
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
            "distribution": [{"range": k, "count": v} for k, v in distribution.items()],
        },
    )
