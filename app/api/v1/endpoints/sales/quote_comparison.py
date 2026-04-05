# -*- coding: utf-8 -*-
"""
报价对比分析 API

提供多版本报价对比和竞品对比功能。
"""

import logging
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.sales import Quote, QuoteItem, QuoteVersion
from app.models.user import User
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


def _calculate_margin(price: Decimal, cost: Decimal) -> float:
    """计算毛利率"""
    if price and price > 0:
        return float((price - cost) / price * 100)
    return 0.0


@router.get("/quotes/{quote_id}/versions/compare", response_model=ResponseModel)
def compare_quote_versions(
    quote_id: int,
    version_ids: List[int] = Query(..., description="要对比的版本ID列表（2-4个）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    对比报价的多个版本

    返回：
    - 各版本基本信息对比
    - 价格/成本/毛利率对比
    - 明细项变化对比
    - 版本间差异高亮
    """
    if len(version_ids) < 2:
        raise HTTPException(status_code=400, detail="至少需要2个版本进行对比")
    if len(version_ids) > 4:
        raise HTTPException(status_code=400, detail="最多支持4个版本对比")

    # 获取报价
    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取各版本
    versions = (
        db.query(QuoteVersion)
        .filter(
            QuoteVersion.quote_id == quote_id,
            QuoteVersion.id.in_(version_ids),
        )
        .order_by(QuoteVersion.version_no)
        .all()
    )

    if len(versions) != len(version_ids):
        raise HTTPException(status_code=400, detail="部分版本不存在")

    # 构建对比数据
    version_data = []
    all_item_names = set()

    for v in versions:
        # 获取明细项
        items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == v.id).all()

        item_map = {}
        for item in items:
            item_name = item.name or item.item_code or f"项目{item.id}"
            all_item_names.add(item_name)
            item_map[item_name] = {
                "qty": float(item.qty or 0),
                "unit_price": float(item.unit_price or 0),
                "amount": float((item.qty or 0) * (item.unit_price or 0)),
                "cost": float(item.cost or 0),
            }

        total_price = float(v.total_price or 0)
        total_cost = float(v.total_cost or 0)

        version_data.append({
            "version_id": v.id,
            "version_no": v.version_no,
            "version_name": v.version_name or f"V{v.version_no}",
            "status": v.status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "total_price": total_price,
            "total_cost": total_cost,
            "margin": _calculate_margin(Decimal(str(total_price)), Decimal(str(total_cost))),
            "item_count": len(items),
            "items": item_map,
        })

    # 计算差异
    base_version = version_data[0]
    differences = []

    for v in version_data[1:]:
        diff = {
            "from_version": base_version["version_no"],
            "to_version": v["version_no"],
            "price_change": v["total_price"] - base_version["total_price"],
            "price_change_pct": (
                (v["total_price"] - base_version["total_price"]) / base_version["total_price"] * 100
                if base_version["total_price"] > 0
                else 0
            ),
            "margin_change": v["margin"] - base_version["margin"],
            "item_changes": [],
        }

        # 对比明细项变化
        for item_name in all_item_names:
            base_item = base_version["items"].get(item_name)
            curr_item = v["items"].get(item_name)

            if base_item and curr_item:
                if base_item["amount"] != curr_item["amount"]:
                    diff["item_changes"].append({
                        "item": item_name,
                        "type": "modified",
                        "old_amount": base_item["amount"],
                        "new_amount": curr_item["amount"],
                        "change": curr_item["amount"] - base_item["amount"],
                    })
            elif base_item and not curr_item:
                diff["item_changes"].append({
                    "item": item_name,
                    "type": "removed",
                    "old_amount": base_item["amount"],
                })
            elif not base_item and curr_item:
                diff["item_changes"].append({
                    "item": item_name,
                    "type": "added",
                    "new_amount": curr_item["amount"],
                })

        differences.append(diff)

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "quote_id": quote_id,
            "quote_code": quote.quote_code,
            "versions": version_data,
            "differences": differences,
            "summary": {
                "version_count": len(versions),
                "price_trend": "up" if version_data[-1]["total_price"] > version_data[0]["total_price"] else "down",
                "margin_trend": "up" if version_data[-1]["margin"] > version_data[0]["margin"] else "down",
            },
        },
    )


@router.get("/quotes/opportunity/{opp_id}/compare", response_model=ResponseModel)
def compare_opportunity_quotes(
    opp_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    对比同一商机的多个报价

    返回：
    - 各报价基本信息
    - 价格/毛利率对比
    - 推荐选择建议
    """
    # 获取商机下所有报价
    quotes = (
        db.query(Quote)
        .options(joinedload(Quote.current_version))
        .filter(Quote.opportunity_id == opp_id)
        .order_by(Quote.created_at.desc())
        .all()
    )

    if not quotes:
        return ResponseModel(
            code=200,
            message="该商机暂无报价",
            data={"items": [], "total": 0},
        )

    # 构建对比数据
    quote_data = []
    for q in quotes:
        v = q.current_version
        if not v:
            continue

        total_price = float(v.total_price or 0)
        total_cost = float(v.total_cost or 0)
        margin = _calculate_margin(Decimal(str(total_price)), Decimal(str(total_cost)))

        quote_data.append({
            "quote_id": q.id,
            "quote_code": q.quote_code,
            "title": q.title or q.quote_code,
            "status": q.status,
            "version_count": q.version_count or 1,
            "current_version_no": v.version_no,
            "total_price": total_price,
            "total_cost": total_cost,
            "margin": round(margin, 2),
            "valid_until": q.valid_until.isoformat() if q.valid_until else None,
            "created_at": q.created_at.isoformat() if q.created_at else None,
        })

    # 排序找出最优报价
    if quote_data:
        # 按毛利率排序
        sorted_by_margin = sorted(quote_data, key=lambda x: x["margin"], reverse=True)
        best_margin = sorted_by_margin[0]

        # 按价格排序
        sorted_by_price = sorted(quote_data, key=lambda x: x["total_price"])
        lowest_price = sorted_by_price[0]

        recommendation = {
            "best_margin": {
                "quote_id": best_margin["quote_id"],
                "quote_code": best_margin["quote_code"],
                "margin": best_margin["margin"],
                "reason": f"毛利率最高 ({best_margin['margin']:.1f}%)",
            },
            "lowest_price": {
                "quote_id": lowest_price["quote_id"],
                "quote_code": lowest_price["quote_code"],
                "total_price": lowest_price["total_price"],
                "reason": f"价格最低 ({lowest_price['total_price']:,.0f} 元)",
            },
        }
    else:
        recommendation = None

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "opportunity_id": opp_id,
            "quotes": quote_data,
            "total": len(quote_data),
            "recommendation": recommendation,
            "comparison": {
                "price_range": {
                    "min": min(q["total_price"] for q in quote_data) if quote_data else 0,
                    "max": max(q["total_price"] for q in quote_data) if quote_data else 0,
                },
                "margin_range": {
                    "min": min(q["margin"] for q in quote_data) if quote_data else 0,
                    "max": max(q["margin"] for q in quote_data) if quote_data else 0,
                },
            },
        },
    )


@router.post("/quotes/competitor-compare", response_model=ResponseModel)
def compare_with_competitor(
    quote_id: int = Query(..., description="我方报价ID"),
    competitor_price: float = Query(..., description="竞品报价金额"),
    competitor_name: Optional[str] = Query(None, description="竞品名称"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    与竞品报价对比

    返回：
    - 价格差异分析
    - 竞争力评估
    - 调价建议
    """
    # 获取我方报价
    quote = (
        db.query(Quote)
        .options(joinedload(Quote.current_version))
        .filter(Quote.id == quote_id)
        .first()
    )

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    v = quote.current_version
    if not v:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    our_price = float(v.total_price or 0)
    our_cost = float(v.total_cost or 0)
    our_margin = _calculate_margin(Decimal(str(our_price)), Decimal(str(our_cost)))

    # 计算差异
    price_diff = our_price - competitor_price
    price_diff_pct = (price_diff / competitor_price * 100) if competitor_price > 0 else 0

    # 竞争力评估
    if price_diff < 0:
        competitiveness = "优势"
        competitiveness_score = min(100, 70 + abs(price_diff_pct))
    elif price_diff_pct <= 5:
        competitiveness = "持平"
        competitiveness_score = 60
    elif price_diff_pct <= 10:
        competitiveness = "略高"
        competitiveness_score = 45
    else:
        competitiveness = "劣势"
        competitiveness_score = max(0, 40 - price_diff_pct)

    # 调价建议
    suggestions = []
    if price_diff > 0:
        # 我方价格更高，计算降价空间
        min_acceptable_price = our_cost / (1 - 0.20)  # 最低20%毛利
        max_discount = our_price - min_acceptable_price

        if max_discount > 0:
            suggestions.append(f"最大可降价空间: {max_discount:,.0f} 元 (保持20%毛利)")
            if competitor_price >= min_acceptable_price:
                suggestions.append(f"可降至竞品价格 {competitor_price:,.0f} 元")
            else:
                suggestions.append(f"⚠️ 竞品价格低于我方成本线，需考虑非价格因素竞争")
        else:
            suggestions.append("⚠️ 当前价格已接近成本，无降价空间")

        suggestions.append("考虑强调产品差异化优势")
        suggestions.append("提供增值服务提升整体价值")
    else:
        suggestions.append("✓ 价格具有竞争力")
        if abs(price_diff_pct) > 10:
            suggestions.append("可考虑适当提价以提高毛利")

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "our_quote": {
                "quote_id": quote.id,
                "quote_code": quote.quote_code,
                "total_price": our_price,
                "total_cost": our_cost,
                "margin": round(our_margin, 2),
            },
            "competitor": {
                "name": competitor_name or "竞品",
                "price": competitor_price,
            },
            "comparison": {
                "price_difference": round(price_diff, 2),
                "price_difference_pct": round(price_diff_pct, 2),
                "competitiveness": competitiveness,
                "competitiveness_score": round(competitiveness_score, 1),
            },
            "suggestions": suggestions,
        },
    )
