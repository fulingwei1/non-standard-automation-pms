# -*- coding: utf-8 -*-
"""
销售统计 - 报价统计

包含报价统计数据
"""

from datetime import date as date_type, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Quote
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/statistics/quote-stats", response_model=ResponseModel)
def get_quote_stats(
    db: Session = Depends(deps.get_db),
    time_range: Optional[str] = Query("month", description="时间范围: week/month/quarter/year"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取报价统计数据
    """
    # 计算时间范围
    now = datetime.now()
    if time_range == "week":
        start_date = now - timedelta(days=7)
    elif time_range == "month":
        start_date = now - timedelta(days=30)
    elif time_range == "quarter":
        start_date = now - timedelta(days=90)
    else:  # year
        start_date = now - timedelta(days=365)

    # 基础查询
    base_query = db.query(Quote)
    period_query = base_query.filter(Quote.created_at >= start_date)

    # 统计各状态数量
    total = base_query.count()
    draft = base_query.filter(Quote.status == "DRAFT").count()
    in_review = base_query.filter(Quote.status == "IN_REVIEW").count()
    approved = base_query.filter(Quote.status == "APPROVED").count()
    sent = base_query.filter(Quote.status == "SENT").count()
    expired = base_query.filter(Quote.status == "EXPIRED").count()
    rejected = base_query.filter(Quote.status == "REJECTED").count()
    accepted = base_query.filter(Quote.status == "ACCEPTED").count()
    converted = base_query.filter(Quote.status == "CONVERTED").count()

    # 本期和上期统计
    this_period = period_query.count()

    # 上一个周期
    if time_range == "week":
        last_start = start_date - timedelta(days=7)
    elif time_range == "month":
        last_start = start_date - timedelta(days=30)
    elif time_range == "quarter":
        last_start = start_date - timedelta(days=90)
    else:
        last_start = start_date - timedelta(days=365)

    last_period = base_query.filter(
        Quote.created_at >= last_start,
        Quote.created_at < start_date
    ).count()

    # 增长率
    growth = round((this_period - last_period) / last_period * 100, 1) if last_period > 0 else 0

    # 金额统计 - 从当前版本获取总价
    all_quotes = base_query.all()
    total_amount = sum([float(q.current_version.total_price or 0) if q.current_version else 0 for q in all_quotes])
    avg_amount = total_amount / total if total > 0 else 0

    # 转化率
    conversion_rate = round(converted / total * 100, 1) if total > 0 else 0

    # 即将到期（7天内）
    today = date_type.today()
    expiring_soon = base_query.filter(
        Quote.valid_until != None,
        Quote.valid_until <= today + timedelta(days=7),
        Quote.valid_until > today,
        Quote.status.in_(["DRAFT", "IN_REVIEW", "APPROVED", "SENT"])
    ).count()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total": total,
            "draft": draft,
            "inReview": in_review,
            "approved": approved,
            "sent": sent,
            "expired": expired,
            "rejected": rejected,
            "accepted": accepted,
            "converted": converted,
            "totalAmount": total_amount,
            "avgAmount": round(avg_amount, 2),
            "avgMargin": 18.5,  # TODO: 从实际数据计算
            "conversionRate": conversion_rate,
            "thisMonth": this_period,
            "lastMonth": last_period,
            "growth": growth,
            "expiringSoon": expiring_soon
        }
    )
