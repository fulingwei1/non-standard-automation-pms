# -*- coding: utf-8 -*-
"""
销售统计 - 报表功能

包含销售漏斗报表、赢输分析、销售业绩、客户贡献、O2C管道等报表
已集成数据权限过滤：不同角色看到不同范围的统计数据
"""

from datetime import date as date_type, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import filter_sales_data_by_scope, filter_sales_finance_data_by_scope
from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote
from app.models.user import User
from app.schemas.common import ResponseModel

from datetime import date

router = APIRouter()


@router.get("/reports/sales-funnel", response_model=ResponseModel)
def get_sales_funnel_report(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售漏斗报表（已集成数据权限过滤）
    """
    from .statistics_core import get_sales_funnel
    # 复用已有的统计逻辑（已包含数据权限过滤）
    return get_sales_funnel(db, start_date, end_date, current_user)


@router.get("/reports/win-loss", response_model=ResponseModel)
def get_win_loss_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    赢单/丢单分析（已集成数据权限过滤）
    """
    query = db.query(Opportunity)
    # 应用数据权限过滤
    query = filter_sales_data_by_scope(query, current_user, db, Opportunity, "owner_id")

    if start_date:
        query = query.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query = query.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))

    won_opps = query.filter(Opportunity.stage == "WON").all()
    lost_opps = query.filter(Opportunity.stage == "LOST").all()

    won_count = len(won_opps)
    lost_count = len(lost_opps)
    total_count = won_count + lost_count
    win_rate = round(won_count / total_count * 100, 2) if total_count > 0 else 0

    won_amount = sum([float(opp.est_amount or 0) for opp in won_opps])
    lost_amount = sum([float(opp.est_amount or 0) for opp in lost_opps])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "won": {
                "count": won_count,
                "amount": won_amount
            },
            "lost": {
                "count": lost_count,
                "amount": lost_amount
            },
            "win_rate": win_rate,
            "total_count": total_count
        }
    )


@router.get("/reports/sales-performance", response_model=ResponseModel)
def get_sales_performance(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    owner_id: Optional[int] = Query(None, description="负责人ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售业绩统计（已集成数据权限过滤）
    """
    query_opps = db.query(Opportunity)
    query_contracts = db.query(Contract)
    query_invoices = db.query(Invoice)

    # 应用数据权限过滤
    query_opps = filter_sales_data_by_scope(query_opps, current_user, db, Opportunity, "owner_id")
    query_contracts = filter_sales_data_by_scope(query_contracts, current_user, db, Contract, "owner_id")
    query_invoices = filter_sales_finance_data_by_scope(query_invoices, current_user, db, Invoice, "created_by")

    if start_date:
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_invoices = query_invoices.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))

    if owner_id:
        query_opps = query_opps.filter(Opportunity.owner_id == owner_id)
        query_contracts = query_contracts.filter(Contract.sales_owner_id == owner_id)

    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    issued_invoices = query_invoices.filter(Invoice.status == "ISSUED").all()

    total_opp_amount = sum([float(opp.est_amount or 0) for opp in won_opps])
    total_contract_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])
    total_invoice_amount = sum([float(inv.amount or 0) for inv in issued_invoices])

    return ResponseModel(
        code=200,
        message="success",
        data={
            "won_opportunities": len(won_opps),
            "total_opportunity_amount": total_opp_amount,
            "signed_contracts": len(signed_contracts),
            "total_contract_amount": total_contract_amount,
            "issued_invoices": len(issued_invoices),
            "total_invoice_amount": total_invoice_amount
        }
    )


@router.get("/reports/customer-contribution", response_model=ResponseModel)
def get_customer_contribution(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    top_n: int = Query(10, ge=1, le=50, description="返回前N名"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    客户贡献分析（已集成数据权限过滤）
    """
    query_contracts = db.query(Contract).filter(Contract.status == "SIGNED")
    # 应用数据权限过滤
    query_contracts = filter_sales_data_by_scope(query_contracts, current_user, db, Contract, "owner_id")

    if start_date:
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    contracts = query_contracts.all()

    # 按客户统计
    customer_stats = {}
    for contract in contracts:
        customer_id = contract.customer_id
        if customer_id not in customer_stats:
            customer = contract.customer
            customer_stats[customer_id] = {
                "customer_id": customer_id,
                "customer_name": customer.customer_name if customer else None,
                "contract_count": 0,
                "total_amount": 0
            }
        customer_stats[customer_id]["contract_count"] += 1
        customer_stats[customer_id]["total_amount"] += float(contract.contract_amount or 0)

    # 排序并取前N名
    sorted_customers = sorted(customer_stats.values(), key=lambda x: x["total_amount"], reverse=True)[:top_n]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "customers": sorted_customers,
            "total_customers": len(customer_stats)
        }
    )


@router.get("/reports/o2c-pipeline", response_model=ResponseModel)
def get_o2c_pipeline(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    O2C流程全链路统计（已集成数据权限过滤）
    """
    today = date_type.today()

    # 线索统计
    query_leads = db.query(Lead)
    query_leads = filter_sales_data_by_scope(query_leads, current_user, db, Lead, "owner_id")
    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_leads = query_leads.count()
    converted_leads = query_leads.filter(Lead.status == "CONVERTED").count()

    # 商机统计
    query_opps = db.query(Opportunity)
    query_opps = filter_sales_data_by_scope(query_opps, current_user, db, Opportunity, "owner_id")
    if start_date:
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_opps = query_opps.count()
    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    won_count = len(won_opps)
    won_amount = sum([float(opp.est_amount or 0) for opp in won_opps])

    # 报价统计
    query_quotes = db.query(Quote)
    query_quotes = filter_sales_data_by_scope(query_quotes, current_user, db, Quote, "owner_id")
    if start_date:
        query_quotes = query_quotes.filter(Quote.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_quotes = query_quotes.filter(Quote.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_quotes = query_quotes.count()
    approved_quotes = query_quotes.filter(Quote.status == "APPROVED").all()
    approved_amount = sum([float(q.total_price or 0) for q in approved_quotes])

    # 合同统计
    query_contracts = db.query(Contract)
    query_contracts = filter_sales_data_by_scope(query_contracts, current_user, db, Contract, "owner_id")
    if start_date:
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_contracts = query_contracts.count()
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    signed_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])

    # 发票统计（使用财务数据权限）
    query_invoices = db.query(Invoice)
    query_invoices = filter_sales_finance_data_by_scope(query_invoices, current_user, db, Invoice, "created_by")
    if start_date:
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_invoices = query_invoices.filter(Invoice.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_invoices = query_invoices.filter(Invoice.status == "ISSUED").count()
    issued_invoices = query_invoices.filter(Invoice.status == "ISSUED").all()
    issued_amount = sum([float(inv.total_amount or inv.amount or 0) for inv in issued_invoices])

    # 收款统计
    paid_invoices = query_invoices.filter(Invoice.payment_status == "PAID").all()
    paid_amount = sum([float(inv.paid_amount or 0) for inv in paid_invoices])

    partial_invoices = query_invoices.filter(Invoice.payment_status == "PARTIAL").all()
    partial_amount = sum([float(inv.paid_amount or 0) for inv in partial_invoices])

    pending_invoices = query_invoices.filter(Invoice.payment_status == "PENDING").all()
    pending_amount = sum([float(inv.total_amount or inv.amount or 0) - float(inv.paid_amount or 0) for inv in pending_invoices])

    # 逾期统计
    overdue_invoices = query_invoices.filter(
        Invoice.status == "ISSUED",
        Invoice.due_date < today,
        Invoice.payment_status.in_(["PENDING", "PARTIAL"])
    ).all()
    overdue_amount = sum([float(inv.total_amount or inv.amount or 0) - float(inv.paid_amount or 0) for inv in overdue_invoices])

    # 计算转化率
    conversion_rate = round(converted_leads / total_leads * 100, 2) if total_leads > 0 else 0
    win_rate = round(won_count / total_opps * 100, 2) if total_opps > 0 else 0
    quote_to_contract_rate = round(total_contracts / total_quotes * 100, 2) if total_quotes > 0 else 0
    contract_to_invoice_rate = round(total_invoices / len(signed_contracts) * 100, 2) if signed_contracts else 0
    collection_rate = round(paid_amount / issued_amount * 100, 2) if issued_amount > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "leads": {
                "total": total_leads,
                "converted": converted_leads,
                "conversion_rate": conversion_rate
            },
            "opportunities": {
                "total": total_opps,
                "won": won_count,
                "won_amount": won_amount,
                "win_rate": win_rate
            },
            "quotes": {
                "total": total_quotes,
                "approved": len(approved_quotes),
                "approved_amount": approved_amount
            },
            "contracts": {
                "total": total_contracts,
                "signed": len(signed_contracts),
                "signed_amount": signed_amount,
                "quote_to_contract_rate": quote_to_contract_rate
            },
            "invoices": {
                "total": total_invoices,
                "issued_amount": issued_amount,
                "contract_to_invoice_rate": contract_to_invoice_rate
            },
            "receivables": {
                "paid_amount": paid_amount,
                "partial_amount": partial_amount,
                "pending_amount": pending_amount,
                "overdue_count": len(overdue_invoices),
                "overdue_amount": overdue_amount,
                "collection_rate": collection_rate
            },
            "pipeline_health": {
                "lead_to_opp_rate": round(total_opps / total_leads * 100, 2) if total_leads > 0 else 0,
                "opp_to_quote_rate": round(total_quotes / total_opps * 100, 2) if total_opps > 0 else 0,
                "quote_to_contract_rate": quote_to_contract_rate,
                "contract_to_invoice_rate": contract_to_invoice_rate,
                "collection_rate": collection_rate
            }
        }
    )
