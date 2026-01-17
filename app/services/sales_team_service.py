# -*- coding: utf-8 -*-
"""
销售团队数据聚合服务

提供个人目标完成率、最近跟进、客户分布等统计，便于前端一次性获取所需信息。
"""

from __future__ import annotations

import logging
from datetime import date as date_type
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.models.sales import (
    Contract,
    Invoice,
    Lead,
    LeadFollowUp,
    Opportunity,
    SalesTarget,
)

logger = logging.getLogger(__name__)


class SalesTeamService:
    """封装销售团队相关的统计逻辑"""

    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate_target_performance(self, target: SalesTarget) -> Tuple[Decimal, float]:
        """
        计算目标的实际完成值与完成率。

        返回：actual_value (Decimal), completion_rate (float百分比)
        """
        period_start, period_end = self.parse_period_value(
            target.period_value, target.target_period
        )
        actual_value = Decimal("0")

        if target.target_type == "LEAD_COUNT":
            lead_query = self.db.query(Lead).filter(Lead.owner_id == target.user_id)
            if period_start:
                lead_query = lead_query.filter(
                    Lead.created_at >= datetime.combine(period_start, datetime.min.time())
                )
            if period_end:
                lead_query = lead_query.filter(
                    Lead.created_at <= datetime.combine(period_end, datetime.max.time())
                )
            actual_value = Decimal(str(lead_query.count()))

        elif target.target_type == "OPPORTUNITY_COUNT":
            opp_query = self.db.query(Opportunity).filter(
                Opportunity.owner_id == target.user_id
            )
            if period_start:
                opp_query = opp_query.filter(
                    Opportunity.created_at
                    >= datetime.combine(period_start, datetime.min.time())
                )
            if period_end:
                opp_query = opp_query.filter(
                    Opportunity.created_at
                    <= datetime.combine(period_end, datetime.max.time())
                )
            actual_value = Decimal(str(opp_query.count()))

        elif target.target_type == "CONTRACT_AMOUNT":
            contract_query = self.db.query(Contract).filter(
                Contract.owner_id == target.user_id
            )
            if period_start:
                contract_query = contract_query.filter(
                    Contract.created_at >= datetime.combine(period_start, datetime.min.time())
                )
            if period_end:
                contract_query = contract_query.filter(
                    Contract.created_at <= datetime.combine(period_end, datetime.max.time())
                )
            contracts = contract_query.all()
            actual_value = Decimal(
                str(sum(float(c.contract_amount or 0) for c in contracts))
            )

        elif target.target_type == "COLLECTION_AMOUNT":
            invoice_query = (
                self.db.query(Invoice)
                .join(Contract)
                .filter(Contract.owner_id == target.user_id)
            )
            if period_start:
                invoice_query = invoice_query.filter(
                    Invoice.paid_date >= period_start
                )
            if period_end:
                invoice_query = invoice_query.filter(
                    Invoice.paid_date <= period_end
                )
            invoices = invoice_query.filter(
                Invoice.payment_status.in_(["PAID", "PARTIAL"])
            ).all()
            actual_value = Decimal(
                str(sum(float(inv.paid_amount or 0) for inv in invoices))
            )

        completion_rate = 0.0
        target_value = Decimal(str(target.target_value or 0))
        if target_value > 0:
            completion_rate = float((actual_value / target_value) * 100)

        return actual_value, completion_rate

    def build_personal_target_map(
        self,
        user_ids: List[int],
        month_value: Optional[str],
        year_value: Optional[str],
    ) -> Dict[int, Dict[str, dict]]:
        """批量计算个人月度/年度合同目标完成情况"""
        if not user_ids:
            return {}

        period_values = [value for value in {month_value, year_value} if value]
        if not period_values:
            return {}

        targets = (
            self.db.query(SalesTarget)
            .filter(
                SalesTarget.target_scope == "PERSONAL",
                SalesTarget.user_id.in_(user_ids),
                SalesTarget.target_period.in_(["MONTHLY", "YEARLY"]),
                SalesTarget.period_value.in_(period_values),
                SalesTarget.status == "ACTIVE",
            )
            .all()
        )

        result: Dict[int, Dict[str, dict]] = {}

        for target in targets:
            # 目前只展示合同金额相关的目标
            if target.target_type not in {"CONTRACT_AMOUNT", "COLLECTION_AMOUNT"}:
                continue

            actual_value, completion_rate = self.calculate_target_performance(target)
            period_key = "monthly" if target.target_period == "MONTHLY" else "yearly"

            user_entry = result.setdefault(target.user_id, {})
            existing = user_entry.get(period_key)

            # 同周期同类型只保留最新一条
            if existing and existing.get("updated_at") and target.updated_at:
                if existing["updated_at"] > target.updated_at:
                    continue

            user_entry[period_key] = {
                "target_id": target.id,
                "target_value": float(target.target_value or 0),
                "actual_value": float(actual_value),
                "completion_rate": round(completion_rate, 1),
                "target_type": target.target_type,
                "period_value": target.period_value,
                "updated_at": target.updated_at or target.created_at,
            }

        return result

    def get_followup_statistics_map(
        self,
        user_ids: List[int],
        start_datetime: Optional[datetime],
        end_datetime: Optional[datetime],
    ) -> Dict[int, dict]:
        """统计不同跟进方式的数量（电话/拜访等）"""
        if not user_ids:
            return {}

        query = (
            self.db.query(
                Lead.owner_id.label("owner_id"),
                LeadFollowUp.follow_up_type.label("follow_up_type"),
                func.count(LeadFollowUp.id).label("count"),
            )
            .join(Lead, LeadFollowUp.lead_id == Lead.id)
            .filter(Lead.owner_id.in_(user_ids))
        )
        if start_datetime:
            query = query.filter(LeadFollowUp.created_at >= start_datetime)
        if end_datetime:
            query = query.filter(LeadFollowUp.created_at <= end_datetime)

        rows = query.group_by(Lead.owner_id, LeadFollowUp.follow_up_type).all()
        result: Dict[int, dict] = {}
        for row in rows:
            entry = result.setdefault(
                row.owner_id,
                {"CALL": 0, "EMAIL": 0, "VISIT": 0, "MEETING": 0, "OTHER": 0, "total": 0},
            )
            key = row.follow_up_type or "OTHER"
            entry[key] = entry.get(key, 0) + int(row.count or 0)
            entry["total"] += int(row.count or 0)
        return result

    def get_lead_quality_stats_map(
        self,
        user_ids: List[int],
        start_datetime: Optional[datetime],
        end_datetime: Optional[datetime],
    ) -> Dict[int, dict]:
        """统计线索数量、转化率、建模覆盖率和信息完整度"""
        if not user_ids:
            return {}

        query = (
            self.db.query(
                Lead.owner_id.label("owner_id"),
                func.count(Lead.id).label("total_leads"),
                func.sum(case((Lead.status == "CONVERTED", 1), else_=0)).label("converted_leads"),
                func.sum(case((Lead.requirement_detail_id.isnot(None), 1), else_=0)).label("modeled_leads"),
                func.avg(func.coalesce(Lead.completeness, 0)).label("avg_completeness"),
            )
            .filter(Lead.owner_id.in_(user_ids))
        )
        if start_datetime:
            query = query.filter(Lead.created_at >= start_datetime)
        if end_datetime:
            query = query.filter(Lead.created_at <= end_datetime)

        rows = query.group_by(Lead.owner_id).all()
        result: Dict[int, dict] = {}
        for row in rows:
            total = int(row.total_leads or 0)
            converted = int(row.converted_leads or 0)
            modeled = int(row.modeled_leads or 0)
            conversion_rate = round((converted / total * 100) if total else 0.0, 1)
            modeling_rate = round((modeled / total * 100) if total else 0.0, 1)
            result[row.owner_id] = {
                "total_leads": total,
                "converted_leads": converted,
                "modeled_leads": modeled,
                "conversion_rate": conversion_rate,
                "modeling_rate": modeling_rate,
                "avg_completeness": round(float(row.avg_completeness or 0.0), 1),
            }
        return result

    def get_opportunity_stats_map(
        self,
        user_ids: List[int],
        start_datetime: Optional[datetime],
        end_datetime: Optional[datetime],
    ) -> Dict[int, dict]:
        """统计商机数量、金额以及预估毛利率"""
        if not user_ids:
            return {}

        query = (
            self.db.query(
                Opportunity.owner_id.label("owner_id"),
                func.count(Opportunity.id).label("opportunity_count"),
                func.sum(func.coalesce(Opportunity.est_amount, 0)).label("pipeline_amount"),
                func.avg(func.coalesce(Opportunity.est_margin, 0)).label("avg_est_margin"),
            )
            .filter(Opportunity.owner_id.in_(user_ids))
        )
        if start_datetime:
            query = query.filter(Opportunity.created_at >= start_datetime)
        if end_datetime:
            query = query.filter(Opportunity.created_at <= end_datetime)

        rows = query.group_by(Opportunity.owner_id).all()
        result: Dict[int, dict] = {}
        for row in rows:
            result[row.owner_id] = {
                "opportunity_count": int(row.opportunity_count or 0),
                "pipeline_amount": float(row.pipeline_amount or 0.0),
                "avg_est_margin": round(float(row.avg_est_margin or 0.0), 1),
            }
        return result

    def get_recent_followups_map(
        self,
        user_ids: List[int],
        start_datetime: Optional[datetime] = None,
        end_datetime: Optional[datetime] = None,
    ) -> Dict[int, dict]:
        """获取每位成员最近一次线索跟进的信息（可选时间范围）"""
        if not user_ids:
            return {}

        latest_query = (
            self.db.query(
                Lead.owner_id.label("owner_id"),
                func.max(LeadFollowUp.created_at).label("last_time"),
            )
            .join(Lead, LeadFollowUp.lead_id == Lead.id)
            .filter(Lead.owner_id.in_(user_ids))
        )
        if start_datetime:
            latest_query = latest_query.filter(LeadFollowUp.created_at >= start_datetime)
        if end_datetime:
            latest_query = latest_query.filter(LeadFollowUp.created_at <= end_datetime)
        latest_subquery = latest_query.group_by(Lead.owner_id).subquery()

        query = self.db.query(
            Lead.owner_id,
            Lead.customer_name,
            Lead.lead_code,
            LeadFollowUp.follow_up_type,
            LeadFollowUp.content,
            LeadFollowUp.created_at,
        ).join(Lead, LeadFollowUp.lead_id == Lead.id)

        if start_datetime:
            query = query.filter(LeadFollowUp.created_at >= start_datetime)
        if end_datetime:
            query = query.filter(LeadFollowUp.created_at <= end_datetime)

        rows = query.join(
            latest_subquery,
            and_(
                latest_subquery.c.owner_id == Lead.owner_id,
                latest_subquery.c.last_time == LeadFollowUp.created_at,
            ),
        ).all()

        result: Dict[int, dict] = {}
        for row in rows:
            result[row.owner_id] = {
                "lead_name": row.customer_name,  # 使用customer_name作为lead_name
                "lead_code": row.lead_code,
                "follow_up_type": row.follow_up_type,
                "content": row.content,
                "created_at": row.created_at,
            }

        return result

    def get_customer_distribution_map(
        self,
        user_ids: List[int],
        start_date: Optional[date_type],
        end_date: Optional[date_type],
    ) -> Dict[int, dict]:
        """统计客户分布及指定区间新增客户数"""
        if not user_ids:
            return {}

        start_datetime = (
            datetime.combine(start_date, datetime.min.time()) if start_date else None
        )
        end_datetime = (
            datetime.combine(end_date, datetime.max.time()) if end_date else None
        )

        # 使用project_type作为分类依据（因为industry字段不存在）
        distributions_query = (
            self.db.query(
                Opportunity.owner_id,
                Opportunity.project_type,
                func.count(Opportunity.id).label("count"),
            )
            .filter(Opportunity.owner_id.in_(user_ids))
        )
        if start_datetime:
            distributions_query = distributions_query.filter(
                Opportunity.created_at >= start_datetime
            )
        if end_datetime:
            distributions_query = distributions_query.filter(
                Opportunity.created_at <= end_datetime
            )
        distributions = distributions_query.group_by(
            Opportunity.owner_id, Opportunity.project_type
        ).all()

        new_customers_query = (
            self.db.query(
                Opportunity.owner_id,
                func.count(func.distinct(Opportunity.customer_id)).label("new_customers"),
            )
            .filter(Opportunity.owner_id.in_(user_ids))
        )
        if start_datetime:
            new_customers_query = new_customers_query.filter(
                Opportunity.created_at >= start_datetime
            )
        if end_datetime:
            new_customers_query = new_customers_query.filter(
                Opportunity.created_at <= end_datetime
            )
        monthly_new = new_customers_query.group_by(Opportunity.owner_id).all()

        result: Dict[int, dict] = {}

        for row in distributions:
            label = row.project_type or "未分类"
            entry = result.setdefault(
                row.owner_id, {"total": 0, "categories": [], "new_customers": 0}
            )
            entry["total"] += row.count
            entry["categories"].append({"label": label, "value": int(row.count)})

        new_map = {row.owner_id: int(row.new_customers or 0) for row in monthly_new}
        for owner_id, new_value in new_map.items():
            entry = result.setdefault(
                owner_id, {"total": 0, "categories": [], "new_customers": 0}
            )
            entry["new_customers"] = new_value

        for entry in result.values():
            total = entry["total"] or 0
            for item in entry["categories"]:
                percentage = (item["value"] / total * 100) if total > 0 else 0
                item["percentage"] = round(percentage, 1)
            entry["categories"].sort(key=lambda x: x["value"], reverse=True)

        return result

    @staticmethod
    def parse_period_value(
        period_value: str, period_type: str
    ) -> Tuple[Optional[date_type], Optional[date_type]]:
        """解析周期值，返回开始与结束日期"""
        try:
            if period_type == "MONTHLY":
                year, month = map(int, period_value.split("-"))
                start_date = date_type(year, month, 1)
                if month == 12:
                    end_date = date_type(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date_type(year, month + 1, 1) - timedelta(days=1)
                return start_date, end_date

            if period_type == "QUARTERLY":
                year, quarter = period_value.split("-Q")
                year = int(year)
                quarter = int(quarter)
                start_month = (quarter - 1) * 3 + 1
                start_date = date_type(year, start_month, 1)
                end_month = quarter * 3
                if end_month == 12:
                    end_date = date_type(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = date_type(year, end_month + 1, 1) - timedelta(days=1)
                return start_date, end_date

            if period_type == "YEARLY":
                year = int(period_value)
                start_date = date_type(year, 1, 1)
                end_date = date_type(year, 12, 31)
                return start_date, end_date

        except Exception:
            logger.debug("解析销售目标周期失败", exc_info=True)

        return None, None
