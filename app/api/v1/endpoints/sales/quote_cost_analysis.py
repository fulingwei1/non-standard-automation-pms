# -*- coding: utf-8 -*-
"""
成本分析 - 自动生成
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
    prefix="/quotes/{quote_id}/cost",
    tags=["cost_analysis"]
)

# 共 3 个路由

# ==================== 成本对比 ====================


@router.get("/quotes/{quote_id}/cost-comparison", response_model=CostComparisonResponse)
def compare_quote_costs(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_ids: Optional[str] = Query(None, description="版本ID列表（逗号分隔），对比多个版本"),
    compare_quote_id: Optional[int] = Query(None, description="对比报价ID（与其他报价对比）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    报价成本对比分析
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取当前版本
    current_version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not current_version:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    current_items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == current_version.id).all()
    current_total_price = float(current_version.total_price or 0)
    current_total_cost = float(current_version.cost_total or 0)
    current_margin = float(current_version.gross_margin or 0)

    current_version_data = {
        "version_no": current_version.version_no,
        "total_price": current_total_price,
        "total_cost": current_total_cost,
        "gross_margin": current_margin
    }

    # 对比数据
    previous_version_data = None
    comparison = None
    breakdown_comparison = []

    # 如果指定了版本ID列表
    if version_ids:
        version_id_list = [int(vid) for vid in version_ids.split(',') if vid.strip()]
        if len(version_id_list) > 0:
            prev_version = db.query(QuoteVersion).filter(QuoteVersion.id == version_id_list[0]).first()
            if prev_version:
                prev_items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == prev_version.id).all()
                prev_total_price = float(prev_version.total_price or 0)
                prev_total_cost = float(prev_version.cost_total or 0)
                prev_margin = float(prev_version.gross_margin or 0)

                previous_version_data = {
                    "version_no": prev_version.version_no,
                    "total_price": prev_total_price,
                    "total_cost": prev_total_cost,
                    "gross_margin": prev_margin
                }

                # 计算对比
                price_change = current_total_price - prev_total_price
                price_change_pct = (price_change / prev_total_price * 100) if prev_total_price > 0 else 0
                cost_change = current_total_cost - prev_total_cost
                cost_change_pct = (cost_change / prev_total_cost * 100) if prev_total_cost > 0 else 0
                margin_change = current_margin - prev_margin
                margin_change_pct = (margin_change / prev_margin * 100) if prev_margin > 0 else 0

                comparison = {
                    "price_change": round(price_change, 2),
                    "price_change_pct": round(price_change_pct, 2),
                    "cost_change": round(cost_change, 2),
                    "cost_change_pct": round(cost_change_pct, 2),
                    "margin_change": round(margin_change, 2),
                    "margin_change_pct": round(margin_change_pct, 2)
                }

                # 按分类对比
                current_by_category = {}
                for item in current_items:
                    category = item.cost_category or "其他"
                    if category not in current_by_category:
                        current_by_category[category] = 0
                    current_by_category[category] += float(item.cost or 0) * float(item.qty or 0)

                prev_by_category = {}
                for item in prev_items:
                    category = item.cost_category or "其他"
                    if category not in prev_by_category:
                        prev_by_category[category] = 0
                    prev_by_category[category] += float(item.cost or 0) * float(item.qty or 0)

                all_categories = set(list(current_by_category.keys()) + list(prev_by_category.keys()))
                for category in all_categories:
                    v1_amount = prev_by_category.get(category, 0)
                    v2_amount = current_by_category.get(category, 0)
                    change = v2_amount - v1_amount
                    change_pct = (change / v1_amount * 100) if v1_amount > 0 else 0
                    breakdown_comparison.append({
                        "category": category,
                        "v1_amount": round(v1_amount, 2),
                        "v2_amount": round(v2_amount, 2),
                        "change": round(change, 2),
                        "change_pct": round(change_pct, 2)
                    })

    return CostComparisonResponse(
        current_version=current_version_data,
        previous_version=previous_version_data,
        comparison=comparison,
        breakdown_comparison=breakdown_comparison if breakdown_comparison else None
    )


# ==================== 成本匹配建议 ====================


@router.post("/quotes/{quote_id}/items/auto-match-cost-suggestions", response_model=CostMatchSuggestionsResponse)
def get_cost_match_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取成本匹配建议（AI生成建议，不直接更新）
    根据物料名称和规格，从采购物料成本清单中生成匹配建议，包含异常检查
    """
    from app.services.cost_match_suggestion_service import (
        process_cost_match_suggestions,
        check_overall_anomalies,
        calculate_summary
    )

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

    # 获取成本清单查询
    cost_query = db.query(PurchaseMaterialCost).filter(
        PurchaseMaterialCost.is_active == True,
        PurchaseMaterialCost.is_standard_part == True
    )

    # 处理成本匹配建议
    suggestions, matched_count, unmatched_count, _, current_total_cost = process_cost_match_suggestions(
        db, items, cost_query
    )

    # 计算当前总价格
    current_total_price = float(version.total_price or 0)

    # 计算建议总成本
    suggested_total_cost = sum([
        float(s.suggested_cost or s.current_cost or 0) *
        float(next((item.qty for item in items if item.id == s.item_id), 0) or 0)
        for s in suggestions
    ])

    # 整体异常检查
    warnings = check_overall_anomalies(
        current_total_price, current_total_cost, suggested_total_cost, items, suggestions
    )

    # 计算汇总
    summary = calculate_summary(current_total_cost, current_total_price, items, suggestions)

    return CostMatchSuggestionsResponse(
        suggestions=suggestions,
        total_items=len(items),
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        warnings=warnings if warnings else None,
        summary=summary
    )


@router.post("/quotes/{quote_id}/items/apply-cost-suggestions", response_model=ResponseModel)
def apply_cost_suggestions(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    version_id: Optional[int] = Query(None, description="版本ID，不指定则使用当前版本"),
    request: ApplyCostSuggestionsRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    应用成本匹配建议（人工确认后应用）
    将用户确认（可能修改过）的建议应用到报价明细中
    """
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    target_version_id = version_id or quote.current_version_id
    if not target_version_id:
        raise HTTPException(status_code=400, detail="报价没有指定版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    item_dict = {item.id: item for item in items}

    applied_count = 0
    updated_cost_records = set()  # 记录已更新的成本记录，避免重复更新使用次数

    for suggestion_data in request.suggestions:
        item_id = suggestion_data.get("item_id")
        if not item_id:
            continue

        item = item_dict.get(item_id)
        if not item:
            continue

        # 应用建议（用户可能已修改）
        if "cost" in suggestion_data:
            item.cost = Decimal(str(suggestion_data["cost"]))
            item.cost_source = "HISTORY"

        if "specification" in suggestion_data:
            item.specification = suggestion_data["specification"]

        if "unit" in suggestion_data:
            item.unit = suggestion_data["unit"]

        if "lead_time_days" in suggestion_data:
            item.lead_time_days = suggestion_data["lead_time_days"]

        if "cost_category" in suggestion_data:
            item.cost_category = suggestion_data["cost_category"]

        db.add(item)
        applied_count += 1

        # 如果应用了成本建议，更新对应的成本记录使用次数
        # 注意：这里需要根据item_name匹配，因为suggestion_data中可能没有cost_record_id
        if "cost" in suggestion_data and item.item_name:
            matched_cost = db.query(PurchaseMaterialCost).filter(
                PurchaseMaterialCost.is_active == True,
                PurchaseMaterialCost.material_name.like(f"%{item.item_name}%")
            ).order_by(desc(PurchaseMaterialCost.match_priority), desc(PurchaseMaterialCost.purchase_date)).first()

            if matched_cost and matched_cost.id not in updated_cost_records:
                matched_cost.usage_count = (matched_cost.usage_count or 0) + 1
                matched_cost.last_used_at = datetime.now()
                db.add(matched_cost)
                updated_cost_records.add(matched_cost.id)

    db.commit()

    # 重新计算总成本
    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == target_version_id).all()
    total_cost = sum([float(item.cost or 0) * float(item.qty or 0) for item in items])
    version = db.query(QuoteVersion).filter(QuoteVersion.id == target_version_id).first()
    if version:
        version.cost_total = total_cost
        total_price = float(version.total_price or 0)
        if total_price > 0:
            version.gross_margin = ((total_price - total_cost) / total_price * 100)
        db.add(version)
        db.commit()

    return ResponseModel(
        code=200,
        message=f"已应用 {applied_count} 项成本建议",
        data={
            "applied_count": applied_count,
            "total_cost": total_cost
        }
    )



