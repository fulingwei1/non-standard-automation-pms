# -*- coding: utf-8 -*-
"""
客户360度视图汇总服务
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Customer, Project, ProjectPaymentPlan
from app.models.sales import Contract, Invoice, Opportunity, Quote, QuoteVersion
from app.models.service import CustomerCommunication


def _decimal(value: Any) -> Decimal:
    """将值安全转换为Decimal"""
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


class Customer360Service:
    """封装客户360视图的聚合逻辑"""

    def __init__(self, db: Session):
        self.db = db

    def build_overview(self, customer_id: int) -> Dict[str, Any]:
        customer = self.db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError("客户不存在")

        projects = (
            self.db.query(Project)
            .filter(Project.customer_id == customer_id)
            .order_by(Project.updated_at.desc())
            .limit(8)
            .all()
        )

        opportunities = (
            self.db.query(Opportunity)
            .filter(Opportunity.customer_id == customer_id)
            .order_by(Opportunity.updated_at.desc())
            .limit(8)
            .all()
        )

        quotes = (
            self.db.query(Quote)
            .filter(Quote.customer_id == customer_id)
            .order_by(Quote.updated_at.desc())
            .limit(8)
            .all()
        )

        contracts = (
            self.db.query(Contract)
            .filter(Contract.customer_id == customer_id)
            .order_by(Contract.updated_at.desc())
            .limit(8)
            .all()
        )

        invoices = (
            self.db.query(Invoice)
            .join(Contract, Invoice.contract_id == Contract.id)
            .filter(Contract.customer_id == customer_id)
            .order_by(Invoice.updated_at.desc())
            .limit(10)
            .all()
        )

        payment_plans = (
            self.db.query(ProjectPaymentPlan)
            .join(Project, ProjectPaymentPlan.project_id == Project.id)
            .filter(Project.customer_id == customer_id)
            .order_by(ProjectPaymentPlan.planned_date.asc())
            .limit(10)
            .all()
        )

        communications = (
            self.db.query(CustomerCommunication)
            .filter(CustomerCommunication.customer_name == customer.customer_name)
            .order_by(CustomerCommunication.communication_date.desc())
            .limit(5)
            .all()
        )

        summary = self._build_summary(customer, projects, opportunities, quotes, contracts, payment_plans, communications)

        return {
            "basic_info": customer,
            "summary": summary,
            "projects": projects,
            "opportunities": opportunities,
            "quotes": quotes,
            "contracts": contracts,
            "invoices": invoices,
            "payment_plans": payment_plans,
            "communications": communications,
        }

    def _build_summary(
        self,
        customer: Customer,
        projects: List[Project],
        opportunities: List[Opportunity],
        quotes: List[Quote],
        contracts: List[Contract],
        payment_plans: List[ProjectPaymentPlan],
        communications: List[CustomerCommunication],
    ) -> Dict[str, Any]:
        total_contract_amount = sum(_decimal(c.contract_amount) for c in contracts)
        open_receivables = Decimal("0")
        for plan in payment_plans:
            if plan.status in ("PENDING", "INVOICED") or _decimal(plan.actual_amount) < _decimal(plan.planned_amount or 0):
                base = _decimal(plan.planned_amount) - _decimal(plan.actual_amount or 0)
                open_receivables += base if base > 0 else Decimal("0")

        pipeline_amount = Decimal("0")
        won_count = 0
        for opp in opportunities:
            if opp.stage == "WON":
                won_count += 1
            elif opp.stage not in ("LOST",):
                pipeline_amount += _decimal(opp.est_amount)

        total_opps = len(opportunities)
        win_rate = float(won_count / total_opps) if total_opps else 0.0

        margins: List[Decimal] = []
        for quote in quotes:
            version: QuoteVersion = quote.current_version
            if version and version.gross_margin is not None:
                margins.append(_decimal(version.gross_margin))
        avg_margin = sum(margins) / len(margins) if margins else None

        active_projects = sum(1 for p in projects if (p.status or "").upper() not in ("CLOSED", "CANCELLED"))

        last_activity_candidates: List[datetime] = []
        for entity in (projects + opportunities + quotes + contracts):
            if getattr(entity, "updated_at", None):
                last_activity_candidates.append(entity.updated_at)
        for comm in communications:
            if comm.communication_date:
                last_activity_candidates.append(datetime.combine(comm.communication_date, datetime.min.time()))

        last_activity = max(last_activity_candidates) if last_activity_candidates else None

        return {
            "total_projects": len(projects),
            "active_projects": active_projects,
            "pipeline_amount": pipeline_amount,
            "total_contract_amount": total_contract_amount,
            "open_receivables": open_receivables,
            "win_rate": round(win_rate * 100, 2),
            "avg_margin": avg_margin,
            "last_activity": last_activity,
        }
