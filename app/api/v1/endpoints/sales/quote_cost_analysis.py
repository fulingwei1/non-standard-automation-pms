# -*- coding: utf-8 -*-
"""
报价成本分析
包含：成本对比、毛利分析、历史趋势
"""

from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion, QuoteItem
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

router = APIRouter()


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
    get_or_404(db, Quote, quote_id, detail="报价不存在")

    versions = db.query(QuoteVersion).filter(
        QuoteVersion.quote_id == quote_id
    ).order_by(QuoteVersion.created_at).all()

    if not versions:
        return ResponseModel(code=200, message="暂无版本数据", data={})

    # 版本趋势
    version_trend = [{
        "version_no": v.version_no,
        "total_price": float(v.total_price) if v.total_price else 0,
        "cost_total": float(v.cost_total) if v.cost_total else 0,
        "gross_margin": float(v.gross_margin) if v.gross_margin else 0,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    } for v in versions]

    # 当前版本的成本结构
    current = versions[-1]
    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == current.id
    ).all()

    # 按类型汇总
    cost_by_type = {}
    for item in items:
        t = item.item_type or "其他"
        if t not in cost_by_type:
            cost_by_type[t] = Decimal('0')
        cost_by_type[t] += item.cost or Decimal('0')

    cost_structure = [
        {"type": k, "cost": float(v), "ratio": round(float(v) / float(current.cost_total) * 100, 2) if current.cost_total else 0}
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

        changes.append({
            "from_version": prev.version_no,
            "to_version": curr.version_no,
            "price_change": price_change,
            "cost_change": cost_change,
            "margin_change": round(margin_change, 2),
        })

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
        }
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
    # 基础查询：近90天的报价
    ninety_days_ago = date.today() - timedelta(days=90)

    result = db.query(
        func.count(Quote.id).label("quote_count"),
        func.avg(QuoteVersion.gross_margin).label("avg_margin"),
        func.min(QuoteVersion.gross_margin).label("min_margin"),
        func.max(QuoteVersion.gross_margin).label("max_margin"),
    ).join(
        QuoteVersion, Quote.current_version_id == QuoteVersion.id
    ).filter(
        Quote.created_at >= ninety_days_ago
    ).first()

    # 毛利率分布
    from sqlalchemy import case as sa_case
    margin_range = sa_case(
        (QuoteVersion.gross_margin < 10, "0-10%"),
        (QuoteVersion.gross_margin < 20, "10-20%"),
        (QuoteVersion.gross_margin < 30, "20-30%"),
        else_="30%+"
    ).label("range")
    distribution = db.query(
        margin_range,
        func.count(Quote.id).label("count")
    ).join(
        QuoteVersion, Quote.current_version_id == QuoteVersion.id
    ).filter(
        Quote.created_at >= ninety_days_ago
    ).group_by(margin_range).all()

    return ResponseModel(
        code=200,
        message="获取成本基准成功",
        data={
            "period": "近90天",
            "quote_count": result.quote_count if result else 0,
            "avg_margin": round(float(result.avg_margin), 2) if result and result.avg_margin else 0,
            "min_margin": round(float(result.min_margin), 2) if result and result.min_margin else 0,
            "max_margin": round(float(result.max_margin), 2) if result and result.max_margin else 0,
            "margin_distribution": [{"range": d.range, "count": d.count} for d in distribution]
        }
    )
