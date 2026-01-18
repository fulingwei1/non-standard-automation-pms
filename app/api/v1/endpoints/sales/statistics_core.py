# -*- coding: utf-8 -*-
"""
销售统计 - 核心统计功能

包含销售漏斗、商机按阶段统计、汇总统计
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/statistics/funnel", response_model=ResponseModel)
def get_sales_funnel(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取销售漏斗统计
    """
    query_leads = db.query(Lead)
    query_opps = db.query(Opportunity)
    query_quotes = db.query(Quote)
    query_contracts = db.query(Contract)

    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_quotes = query_quotes.filter(Quote.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_quotes = query_quotes.filter(Quote.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    # 统计各阶段数量
    leads_count = query_leads.count()
    opps_count = query_opps.count()
    quotes_count = query_quotes.count()
    contracts_count = query_contracts.count()

    # 统计金额
    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    total_opp_amount = sum([float(opp.est_amount or 0) for opp in won_opps])

    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    total_contract_amount = sum([float(contract.contract_amount or 0) for contract in signed_contracts])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "leads": leads_count,
            "opportunities": opps_count,
            "quotes": quotes_count,
            "contracts": contracts_count,
            "total_opportunity_amount": total_opp_amount,
            "total_contract_amount": total_contract_amount,
            "conversion_rates": {
                "lead_to_opp": round(opps_count / leads_count * 100, 2) if leads_count > 0 else 0,
                "opp_to_quote": round(quotes_count / opps_count * 100, 2) if opps_count > 0 else 0,
                "quote_to_contract": round(contracts_count / quotes_count * 100, 2) if quotes_count > 0 else 0,
            }
        }
    )


@router.get("/statistics/opportunities-by-stage", response_model=ResponseModel)
def get_opportunities_by_stage(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按阶段统计商机
    """
    stages = ["DISCOVERY", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    result = {}

    from sqlalchemy import func
    for stage in stages:
        count = db.query(Opportunity).filter(Opportunity.stage == stage).count()
        total_amount = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage).scalar() or 0
        result[stage] = {
            "count": count,
            "total_amount": float(total_amount)
        }

    return ResponseModel(
        code=200,
        message="success",
        data=result
    )


@router.get("/statistics/summary", response_model=ResponseModel)
def get_sales_summary(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取销售汇总统计
    """
    query_leads = db.query(Lead)
    query_opps = db.query(Opportunity)
    query_contracts = db.query(Contract)
    query_invoices = db.query(Invoice)

    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_invoices = query_invoices.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))

    # 线索统计
    total_leads = query_leads.count()
    converted_leads = query_leads.filter(Lead.status == "CONVERTED").count()

    # 商机统计
    total_opportunities = query_opps.count()
    won_opportunities = query_opps.filter(Opportunity.stage == "WON").count()

    # 合同统计
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    total_contract_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])

    # 发票统计
    paid_invoices = query_invoices.filter(Invoice.payment_status == "PAID").all()
    paid_amount = sum([float(inv.paid_amount or 0) for inv in paid_invoices])

    # 计算转化率
    conversion_rate = round((converted_leads / total_leads * 100), 2) if total_leads > 0 else 0
    win_rate = round((won_opportunities / total_opportunities * 100), 2) if total_opportunities > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "total_opportunities": total_opportunities,
            "won_opportunities": won_opportunities,
            "total_contract_amount": total_contract_amount,
            "paid_amount": paid_amount,
            "conversion_rate": conversion_rate,
            "win_rate": win_rate,
        }
    )
