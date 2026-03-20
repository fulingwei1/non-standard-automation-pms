# -*- coding: utf-8 -*-
"""
报价统计服务

统一处理报价统计口径，避免多个端点重复实现并出现权限/性能偏差。
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.core.sales_permissions import filter_sales_data_by_scope
from app.models.sales import Quote, QuoteVersion
from app.models.user import User


class QuoteStatisticsService:
    """报价统计聚合服务。"""

    EXPIRING_STATUSES = ("DRAFT", "IN_REVIEW", "APPROVED", "SENT")

    def __init__(self, db: Session):
        self.db = db

    def get_statistics(
        self,
        current_user: User,
        time_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取当前用户数据范围内的报价统计。"""
        today = date.today()
        scoped_query = filter_sales_data_by_scope(
            self.db.query(Quote),
            current_user,
            self.db,
            Quote,
            "owner_id",
        )

        (
            total,
            draft,
            in_review,
            approved,
            sent,
            expired,
            rejected,
            accepted,
            converted,
            total_amount_raw,
            avg_margin_raw,
            expiring_soon,
        ) = (
            scoped_query.outerjoin(QuoteVersion, Quote.current_version_id == QuoteVersion.id)
            .with_entities(
                func.count(Quote.id),
                func.coalesce(func.sum(case((Quote.status == "DRAFT", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "IN_REVIEW", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "APPROVED", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "SENT", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "EXPIRED", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "REJECTED", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "ACCEPTED", 1), else_=0)), 0),
                func.coalesce(func.sum(case((Quote.status == "CONVERTED", 1), else_=0)), 0),
                func.coalesce(func.sum(QuoteVersion.total_price), 0),
                func.avg(QuoteVersion.gross_margin),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    Quote.valid_until.is_not(None),
                                    Quote.valid_until <= today + timedelta(days=7),
                                    Quote.valid_until > today,
                                    Quote.status.in_(self.EXPIRING_STATUSES),
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ),
            )
            .one()
        )

        total = int(total or 0)
        total_amount = float(total_amount_raw or 0)
        avg_margin = round(float(avg_margin_raw or 0), 2)

        data = {
            "total": total,
            "draft": int(draft or 0),
            "inReview": int(in_review or 0),
            "approved": int(approved or 0),
            "sent": int(sent or 0),
            "expired": int(expired or 0),
            "rejected": int(rejected or 0),
            "accepted": int(accepted or 0),
            "converted": int(converted or 0),
            "totalAmount": round(total_amount, 2),
            "avgAmount": round(total_amount / total, 2) if total > 0 else 0,
            "avgMargin": avg_margin,
            "conversionRate": round(int(converted or 0) / total * 100, 1) if total > 0 else 0,
            "expiringSoon": int(expiring_soon or 0),
        }

        if time_range:
            current_period, previous_period, growth = self._get_period_stats(
                scoped_query,
                time_range=time_range,
            )
            data.update(
                {
                    "currentPeriod": current_period,
                    "previousPeriod": previous_period,
                    "growth": growth,
                }
            )

        return data

    def _get_period_stats(self, scoped_query, time_range: str) -> Tuple[int, int, float]:
        start_date, previous_start = self._resolve_period_range(time_range)

        current_period = scoped_query.filter(Quote.created_at >= start_date).count()
        previous_period = scoped_query.filter(
            Quote.created_at >= previous_start,
            Quote.created_at < start_date,
        ).count()
        growth = (
            round((current_period - previous_period) / previous_period * 100, 1)
            if previous_period > 0
            else 0
        )
        return current_period, previous_period, growth

    @staticmethod
    def _resolve_period_range(time_range: str) -> Tuple[datetime, datetime]:
        now = datetime.now()
        normalized = (time_range or "month").strip().lower()

        if normalized == "week":
            delta = timedelta(days=7)
        elif normalized == "quarter":
            delta = timedelta(days=90)
        elif normalized == "year":
            delta = timedelta(days=365)
        else:
            delta = timedelta(days=30)

        start_date = now - delta
        return start_date, start_date - delta
