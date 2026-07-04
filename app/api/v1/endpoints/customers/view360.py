# -*- coding: utf-8 -*-
"""
客户360视图
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project import (
    Customer360CommunicationItem,
    Customer360ContractItem,
    Customer360InvoiceItem,
    Customer360OpportunityItem,
    Customer360PaymentPlanItem,
    Customer360ProjectItem,
    Customer360QuoteItem,
    Customer360Response,
    Customer360Summary,
)
from app.services.customer_360_service import Customer360Service
from app.services.data_scope import DataScopeService

router = APIRouter()


@router.get("/{customer_id}/360", response_model=Customer360Response)
def get_customer_360_overview(
    *,
    db: Session = Depends(deps.get_db),
    customer_id: int,
    current_user: User = Depends(security.require_permission("customer:read")),
) -> Any:
    """
    获取客户360视图信息
    """
    if not DataScopeService.check_customer_access(db, current_user, customer_id):
        raise HTTPException(status_code=403, detail="无权访问该客户的数据")

    service = Customer360Service(db)
    try:
        overview = service.build_overview(customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    customer = overview["basic_info"]
    summary = overview["summary"]
    projects = [
        Customer360ProjectItem(
            project_id=p.id,
            project_code=p.project_code,
            project_name=p.project_name,
            stage=p.stage,
            status=p.status,
            progress_pct=p.progress_pct,
            contract_amount=p.contract_amount,
            planned_end_date=p.planned_end_date,
        )
        for p in overview["projects"]
    ]

    stage_probability = {
        "DISCOVERY": 0.15,
        "QUALIFICATION": 0.3,
        "PROPOSAL": 0.55,
        "NEGOTIATION": 0.75,
        "WON": 1.0,
        "LOST": 0.0,
        "ON_HOLD": 0.1,
    }
    opportunities = [
        Customer360OpportunityItem(
            opportunity_id=o.id,
            opp_code=o.opp_code,
            opp_name=o.opp_name,
            stage=o.stage,
            est_amount=o.est_amount,
            owner_name=o.owner.real_name if o.owner else None,
            win_probability=stage_probability.get(o.stage or "", 0) * 100,
            updated_at=o.updated_at,
        )
        for o in overview["opportunities"]
    ]

    quotes = []
    for quote in overview["quotes"]:
        current_version = quote.current_version
        quotes.append(
            Customer360QuoteItem(
                quote_id=quote.id,
                quote_code=quote.quote_code,
                status=quote.status,
                total_price=current_version.total_price if current_version else None,
                gross_margin=current_version.gross_margin if current_version else None,
                owner_name=quote.owner.real_name if quote.owner else None,
                valid_until=quote.valid_until,
            )
        )

    contracts = [
        Customer360ContractItem(
            contract_id=c.id,
            contract_code=c.contract_code,
            status=c.status,
            contract_amount=getattr(c, "total_amount", None) or getattr(c, "contract_amount", None),
            signed_date=c.signing_date,
            project_code=c.project.project_code if c.project else None,
        )
        for c in overview["contracts"]
    ]

    invoices = [
        Customer360InvoiceItem(
            invoice_id=i.id,
            invoice_code=i.invoice_code,
            status=i.status,
            total_amount=i.total_amount,
            issue_date=i.issue_date,
            paid_amount=i.paid_amount,
        )
        for i in overview["invoices"]
    ]

    payment_plans = [
        Customer360PaymentPlanItem(
            plan_id=p.id,
            project_id=p.project_id,
            payment_name=p.payment_name,
            status=p.status,
            planned_amount=p.planned_amount,
            actual_amount=p.actual_amount,
            planned_date=p.planned_date,
            actual_date=p.actual_date,
        )
        for p in overview["payment_plans"]
    ]

    communications = [
        Customer360CommunicationItem(
            communication_id=comm.id,
            topic=comm.topic,
            communication_type=comm.communication_type,
            communication_date=comm.communication_date,
            owner_name=comm.created_by_name,
            follow_up_required=comm.follow_up_required,
        )
        for comm in overview["communications"]
    ]

    orders = [
        {
            "id": order.order_no or str(order.id),
            "date": order.created_at.date() if order.created_at else None,
            "product": order.project.project_name if order.project else order.project_no,
            "amount": order.order_amount,
            "status": order.order_status,
            "deliveryDate": order.promised_date or order.required_date,
        }
        for order in overview.get("orders", [])
    ]

    payments = [
        {
            "id": f"PAY-{plan.id}",
            "date": plan.actual_date or plan.planned_date,
            "amount": plan.planned_amount,
            "method": plan.payment_type,
            "status": plan.status,
            "orderId": plan.project.project_code if plan.project else plan.project_id,
        }
        for plan in overview.get("payments", [])
    ]

    satisfactions = [
        {
            "id": item.survey_no or str(item.id),
            "date": item.response_date or item.survey_date,
            "type": item.survey_type,
            "score": item.overall_score,
            "feedback": item.feedback,
            "improvements": item.suggestions,
        }
        for item in overview.get("satisfactions", [])
    ]

    services = []
    for ticket in overview.get("services", []):
        response_time = None
        if ticket.response_time and ticket.reported_time:
            response_time = round(
                (ticket.response_time - ticket.reported_time).total_seconds() / 3600,
                2,
            )
        services.append(
            {
                "id": ticket.ticket_no or str(ticket.id),
                "date": ticket.reported_time.date() if ticket.reported_time else None,
                "type": ticket.problem_type or ticket.ticket_type,
                "issue": ticket.problem_desc,
                "resolution": ticket.solution,
                "satisfaction": ticket.satisfaction,
                "responseTime": response_time,
                "status": ticket.status,
            }
        )

    return Customer360Response(
        basic_info=customer,
        summary=Customer360Summary(**summary),
        projects=projects,
        opportunities=opportunities,
        quotes=quotes,
        contracts=contracts,
        invoices=invoices,
        payment_plans=payment_plans,
        communications=communications,
        orders=orders,
        payments=payments,
        satisfactions=satisfactions,
        services=services,
    )
