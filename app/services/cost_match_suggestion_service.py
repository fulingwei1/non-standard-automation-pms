# -*- coding: utf-8 -*-
"""
成本匹配建议服务
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_keyword_filter
from app.models.sales.quotes import PurchaseMaterialCost
from app.models.sales import QuoteItem
from app.schemas.sales import CostMatchSuggestion, PurchaseMaterialCostResponse


def check_cost_anomalies(
    db: Session, item: QuoteItem, cost_query, current_cost: float
) -> List[str]:
    """
    检查成本异常

    Returns:
        List[str]: 警告信息列表
    """
    warnings = []

    if not item.item_name:
        return warnings

    historical_costs = apply_keyword_filter(
        cost_query,
        PurchaseMaterialCost,
        item.item_name,
        "material_name",
        use_ilike=False,
    ).all()

    if not historical_costs:
        return warnings

    avg_cost = sum([float(c.unit_cost or 0) for c in historical_costs]) / len(
        historical_costs
    )
    max_cost = max([float(c.unit_cost or 0) for c in historical_costs])
    min_cost = min([float(c.unit_cost or 0) for c in historical_costs])

    if current_cost > max_cost * 1.5:
        warnings.append(
            f"成本异常偏高：当前{current_cost}，历史最高{max_cost}，超出50%"
        )
    elif current_cost < min_cost * 0.5:
        warnings.append(
            f"成本异常偏低：当前{current_cost}，历史最低{min_cost}，低于50%"
        )
    elif abs(current_cost - avg_cost) / avg_cost > 0.3:
        warnings.append(
            f"成本偏差较大：当前{current_cost}，历史平均{avg_cost:.2f}，偏差超过30%"
        )

    return warnings


def find_matching_cost(
    db: Session, item: QuoteItem, cost_query
) -> Tuple[Optional[PurchaseMaterialCost], Optional[int], Optional[str]]:
    """
    查找匹配的成本记录

    Returns:
        Tuple[Optional[PurchaseMaterialCost], Optional[int], Optional[str]]: (匹配的成本记录, 匹配分数, 匹配原因)
    """
    if not item.item_name:
        return None, None, None

    # 1. 精确匹配
    exact_match = (
        cost_query.filter(PurchaseMaterialCost.material_name == item.item_name)
        .order_by(
            desc(PurchaseMaterialCost.match_priority),
            desc(PurchaseMaterialCost.purchase_date),
        )
        .first()
    )

    if exact_match:
        return exact_match, 100, "精确匹配物料名称"

    # 2. 模糊匹配
    fuzzy_matches = (
        apply_keyword_filter(
            cost_query,
            PurchaseMaterialCost,
            item.item_name,
            "material_name",
            use_ilike=False,
        )
        .order_by(
            desc(PurchaseMaterialCost.match_priority),
            desc(PurchaseMaterialCost.purchase_date),
        )
        .limit(1)
        .all()
    )

    if fuzzy_matches:
        return fuzzy_matches[0], 80, "模糊匹配物料名称"

    # 3. 关键词匹配
    keywords = item.item_name.split()
    for keyword in keywords:
        if len(keyword) > 2:
            keyword_matches = (
                apply_keyword_filter(
                    cost_query,
                    PurchaseMaterialCost,
                    keyword,
                    ["material_name", "match_keywords"],
                    use_ilike=False,
                )
                .order_by(
                    desc(PurchaseMaterialCost.match_priority),
                    desc(PurchaseMaterialCost.usage_count),
                )
                .limit(1)
                .all()
            )

            if keyword_matches:
                return keyword_matches[0], 60, f"关键词匹配：{keyword}"

    return None, None, None


def build_cost_suggestion(
    item: QuoteItem,
    current_cost: float,
    matched_cost: Optional[PurchaseMaterialCost],
    match_score: Optional[int],
    reason: Optional[str],
    warnings: List[str],
) -> CostMatchSuggestion:
    """
    构建成本匹配建议

    Returns:
        CostMatchSuggestion: 成本匹配建议对象
    """
    suggestion = CostMatchSuggestion(
        item_id=item.id,
        item_name=item.item_name or "",
        current_cost=Decimal(str(current_cost)) if current_cost > 0 else None,
        suggested_cost=Decimal(str(matched_cost.unit_cost)) if matched_cost else None,
        match_score=match_score,
        suggested_specification=matched_cost.specification if matched_cost else None,
        suggested_unit=matched_cost.unit if matched_cost else None,
        suggested_lead_time_days=matched_cost.lead_time_days if matched_cost else None,
        suggested_cost_category=matched_cost.material_type if matched_cost else None,
        reason=reason,
        warnings=warnings,
    )

    # 添加匹配到的成本记录信息
    if matched_cost:
        matched_cost_dict = {
            **{
                c.name: getattr(matched_cost, c.name)
                for c in matched_cost.__table__.columns
            },
            "submitter_name": matched_cost.submitter.real_name
            if matched_cost.submitter
            else None,
        }
        suggestion.matched_cost_record = PurchaseMaterialCostResponse(
            **matched_cost_dict
        )

    return suggestion


def check_overall_anomalies(
    current_total_price: float,
    current_total_cost: float,
    suggested_total_cost: float,
    items: List[QuoteItem],
    suggestions: List[CostMatchSuggestion],
) -> List[str]:
    """
    整体异常检查

    Returns:
        List[str]: 警告信息列表
    """
    warnings = []

    if current_total_price <= 0 or suggested_total_cost <= 0:
        return warnings

    suggested_margin = (
        (current_total_price - suggested_total_cost) / current_total_price * 100
    )
    current_margin = (
        ((current_total_price - current_total_cost) / current_total_price * 100)
        if current_total_cost > 0
        else None
    )

    if suggested_margin < 10:
        warnings.append(
            f"建议成本计算后毛利率仅{suggested_margin:.2f}%，低于10%，存在风险"
        )
    elif current_margin and abs(suggested_margin - current_margin) > 10:
        warnings.append(
            f"建议成本与当前成本差异较大：当前毛利率{current_margin:.2f}%，建议毛利率{suggested_margin:.2f}%"
        )

    return warnings


def calculate_summary(
    current_total_cost: float,
    current_total_price: float,
    items: List[QuoteItem],
    suggestions: List[CostMatchSuggestion],
) -> Dict[str, Any]:
    """
    计算汇总信息

    Returns:
        Dict[str, Any]: 汇总信息
    """
    suggested_total_cost = sum(
        [
            float(s.suggested_cost or s.current_cost or 0)
            * float(next((item.qty for item in items if item.id == s.item_id), 0) or 0)
            for s in suggestions
        ]
    )

    summary = {
        "current_total_cost": current_total_cost,
        "suggested_total_cost": suggested_total_cost,
        "current_total_price": current_total_price,
        "current_margin": (
            (current_total_price - current_total_cost) / current_total_price * 100
        )
        if current_total_price > 0 and current_total_cost > 0
        else None,
        "suggested_margin": None,
    }

    if summary["suggested_total_cost"] > 0 and current_total_price > 0:
        summary["suggested_margin"] = (
            (current_total_price - summary["suggested_total_cost"])
            / current_total_price
            * 100
        )

    return summary


def process_cost_match_suggestions(
    db: Session, items: List[QuoteItem], cost_query
) -> Tuple[List[CostMatchSuggestion], int, int, List[str], float]:
    """
    处理成本匹配建议

    Returns:
        Tuple[List[CostMatchSuggestion], int, int, List[str], float]:
        (建议列表, 匹配数量, 未匹配数量, 警告列表, 当前总成本)
    """
    suggestions = []
    matched_count = 0
    unmatched_count = 0

    # 计算当前总成本
    current_total_cost = sum(
        [float(item.cost or 0) * float(item.qty or 0) for item in items]
    )

    for item in items:
        current_cost = float(item.cost or 0)
        item_warnings = []
        matched_cost = None
        match_score = None
        reason = None

        # 如果已有成本，检查异常
        if current_cost > 0:
            item_warnings = check_cost_anomalies(db, item, cost_query, current_cost)
        else:
            # 尝试匹配成本
            matched_cost, match_score, reason = find_matching_cost(db, item, cost_query)

            if matched_cost:
                matched_count += 1
            else:
                unmatched_count += 1
                item_warnings.append("未找到匹配的成本记录，请手动填写")

        # 构建建议
        suggestion = build_cost_suggestion(
            item, current_cost, matched_cost, match_score, reason, item_warnings
        )
        suggestions.append(suggestion)

    return suggestions, matched_count, unmatched_count, [], current_total_cost
