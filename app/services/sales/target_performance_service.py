# -*- coding: utf-8 -*-
"""
销售目标绩效计算服务

为旧版 SalesTarget 提供真实完成值与完成率计算，避免接口继续返回占位值。
"""

import logging
from datetime import date, datetime, time
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.common.date_range import get_month_range_by_ym
from app.models.organization import Department
from app.models.sales import Contract, Invoice, Lead, Opportunity, SalesTarget, SalesTeamMember
from app.models.user import User

logger = logging.getLogger(__name__)


class SalesTargetPerformanceService:
    """旧版销售目标的实际完成值计算服务。"""

    VALID_CONTRACT_STATUSES = (
        "SIGNED",
        "signed",
        "ACTIVE",
        "active",
        "EXECUTING",
        "executing",
        "COMPLETED",
        "completed",
    )
    VALID_COLLECTION_STATUSES = ("PAID", "PARTIAL")

    def __init__(self, db: Session):
        self.db = db
        self._period_cache: Dict[Tuple[Optional[str], Optional[str]], Optional[Tuple[date, date]]] = {}
        self._scope_user_ids_cache: Dict[Tuple[str, Optional[int]], List[int]] = {}

    def calculate_target(self, target: SalesTarget) -> Dict[str, object]:
        """计算单个目标的实际完成值和完成率。"""
        period_range = self._resolve_period_range(target.target_period, target.period_value)
        if period_range is None:
            return {
                "actual_value": Decimal("0"),
                "completion_rate": 0.0,
                "start_date": None,
                "end_date": None,
                "user_ids": [],
            }

        start_date, end_date = period_range
        user_ids = self._resolve_target_user_ids(target)
        actual_value = self._calculate_actual_value(
            target_type=target.target_type,
            user_ids=user_ids,
            start_date=start_date,
            end_date=end_date,
        )

        target_value = Decimal(str(target.target_value or 0))
        completion_rate = 0.0
        if target_value > 0:
            completion_rate = round(float(actual_value / target_value * Decimal("100")), 2)

        return {
            "actual_value": actual_value,
            "completion_rate": completion_rate,
            "start_date": start_date,
            "end_date": end_date,
            "user_ids": user_ids,
        }

    def _resolve_period_range(
        self,
        target_period: Optional[str],
        period_value: Optional[str],
    ) -> Optional[Tuple[date, date]]:
        cache_key = (target_period, period_value)
        if cache_key in self._period_cache:
            return self._period_cache[cache_key]

        normalized_period = (target_period or "").upper()
        if normalized_period not in {"MONTHLY", "QUARTERLY", "YEARLY"}:
            if period_value and "-Q" in period_value:
                normalized_period = "QUARTERLY"
            elif period_value and len(period_value) == 7 and period_value.count("-") == 1:
                normalized_period = "MONTHLY"
            elif period_value and len(period_value) == 4:
                normalized_period = "YEARLY"

        try:
            if normalized_period == "MONTHLY":
                year, month = map(int, (period_value or "").split("-"))
                result = get_month_range_by_ym(year, month)
            elif normalized_period == "QUARTERLY":
                year_text, quarter_text = (period_value or "").split("-Q")
                year = int(year_text)
                quarter = int(quarter_text)
                if quarter not in {1, 2, 3, 4}:
                    raise ValueError(f"invalid quarter: {quarter}")
                start_month = (quarter - 1) * 3 + 1
                start_date, _ = get_month_range_by_ym(year, start_month)
                _, end_date = get_month_range_by_ym(year, start_month + 2)
                result = (start_date, end_date)
            elif normalized_period == "YEARLY":
                year = int(period_value or "")
                result = (date(year, 1, 1), date(year, 12, 31))
            else:
                raise ValueError(f"unsupported period: {target_period}")
        except (TypeError, ValueError, AttributeError) as exc:
            logger.warning(
                "无法解析销售目标周期，target_period=%s period_value=%s error=%s",
                target_period,
                period_value,
                exc,
            )
            result = None

        self._period_cache[cache_key] = result
        return result

    def _resolve_target_user_ids(self, target: SalesTarget) -> List[int]:
        scope = (target.target_scope or "").upper()

        if scope == "PERSONAL" and target.user_id:
            return [target.user_id]

        if scope == "TEAM" and target.team_id:
            return self._resolve_team_user_ids(target.team_id)

        if scope == "DEPARTMENT" and target.department_id:
            return self._resolve_department_user_ids(target.department_id)

        if target.user_id:
            return [target.user_id]
        if target.team_id:
            return self._resolve_team_user_ids(target.team_id)
        if target.department_id:
            return self._resolve_department_user_ids(target.department_id)
        return []

    def _resolve_team_user_ids(self, team_id: int) -> List[int]:
        cache_key = ("TEAM", team_id)
        if cache_key in self._scope_user_ids_cache:
            return self._scope_user_ids_cache[cache_key]

        user_ids = [
            user_id
            for (user_id,) in (
                self.db.query(SalesTeamMember.user_id)
                .filter(
                    SalesTeamMember.team_id == team_id,
                    SalesTeamMember.is_active.is_(True),
                )
                .distinct()
                .all()
            )
        ]
        self._scope_user_ids_cache[cache_key] = user_ids
        return user_ids

    def _resolve_department_user_ids(self, department_id: int) -> List[int]:
        cache_key = ("DEPARTMENT", department_id)
        if cache_key in self._scope_user_ids_cache:
            return self._scope_user_ids_cache[cache_key]

        dept_name = (
            self.db.query(Department.dept_name).filter(Department.id == department_id).scalar()
        )
        query = self.db.query(User.id).filter(User.is_active.is_(True))
        if dept_name:
            query = query.filter(
                or_(
                    User.department_id == department_id,
                    User.department == dept_name,
                )
            )
        else:
            query = query.filter(User.department_id == department_id)

        user_ids = [user_id for (user_id,) in query.distinct().all()]
        self._scope_user_ids_cache[cache_key] = user_ids
        return user_ids

    def _calculate_actual_value(
        self,
        *,
        target_type: Optional[str],
        user_ids: List[int],
        start_date: date,
        end_date: date,
    ) -> Decimal:
        if not user_ids:
            return Decimal("0")

        normalized_type = (target_type or "").upper()
        start_datetime = datetime.combine(start_date, time.min)
        end_datetime = datetime.combine(end_date, time.max)

        if normalized_type == "LEAD_COUNT":
            total = (
                self.db.query(func.count(Lead.id))
                .filter(
                    Lead.owner_id.in_(user_ids),
                    Lead.created_at >= start_datetime,
                    Lead.created_at <= end_datetime,
                )
                .scalar()
            )
            return Decimal(str(total or 0))

        if normalized_type == "OPPORTUNITY_COUNT":
            total = (
                self.db.query(func.count(Opportunity.id))
                .filter(
                    Opportunity.owner_id.in_(user_ids),
                    Opportunity.created_at >= start_datetime,
                    Opportunity.created_at <= end_datetime,
                )
                .scalar()
            )
            return Decimal(str(total or 0))

        if normalized_type == "CONTRACT_AMOUNT":
            total = (
                self.db.query(func.coalesce(func.sum(Contract.total_amount), 0))
                .filter(
                    Contract.sales_owner_id.in_(user_ids),
                    Contract.signing_date.isnot(None),
                    Contract.signing_date >= start_date,
                    Contract.signing_date <= end_date,
                    Contract.status.in_(self.VALID_CONTRACT_STATUSES),
                )
                .scalar()
            )
            return Decimal(str(total or 0))

        if normalized_type == "COLLECTION_AMOUNT":
            total = (
                self.db.query(func.coalesce(func.sum(Invoice.paid_amount), 0))
                .join(Contract, Invoice.contract_id == Contract.id)
                .filter(
                    Contract.sales_owner_id.in_(user_ids),
                    Invoice.paid_date.isnot(None),
                    Invoice.paid_date >= start_date,
                    Invoice.paid_date <= end_date,
                    Invoice.payment_status.in_(self.VALID_COLLECTION_STATUSES),
                )
                .scalar()
            )
            return Decimal(str(total or 0))

        logger.info("未支持的销售目标类型，按 0 处理: %s", target_type)
        return Decimal("0")


__all__ = ["SalesTargetPerformanceService"]
