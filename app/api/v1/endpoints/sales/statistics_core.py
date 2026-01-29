# -*- coding: utf-8 -*-
"""
销售统计 - 核心统计功能

包含销售漏斗、商机按阶段统计、汇总统计
已集成数据权限过滤：不同角色看到不同范围的统计数据
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import filter_sales_data_by_scope
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
    获取销售漏斗统计（已集成数据权限过滤）
    """
    # 构建基础查询
    query_leads = db.query(Lead)
    query_opps = db.query(Opportunity)
    query_quotes = db.query(Quote)
    query_contracts = db.query(Contract)

    # 应用数据权限过滤
    query_leads = filter_sales_data_by_scope(query_leads, current_user, db, Lead, "owner_id")
    query_opps = filter_sales_data_by_scope(query_opps, current_user, db, Opportunity, "owner_id")
    query_quotes = filter_sales_data_by_scope(query_quotes, current_user, db, Quote, "owner_id")
    query_contracts = filter_sales_data_by_scope(query_contracts, current_user, db, Contract, "owner_id")

    # 日期过滤
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
    按阶段统计商机（已集成数据权限过滤）
    """
    stages = ["DISCOVERY", "QUALIFIED", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    result = {}

    from sqlalchemy import func

    # 构建基础查询并应用数据权限过滤
    base_query = db.query(Opportunity)
    base_query = filter_sales_data_by_scope(base_query, current_user, db, Opportunity, "owner_id")

    for stage in stages:
        stage_query = base_query.filter(Opportunity.stage == stage)
        count = stage_query.count()

        # 对于金额统计，需要重新构建查询
        amount_query = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage)
        # 应用数据权限过滤（需要子查询方式）
        filtered_ids = [opp.id for opp in base_query.filter(Opportunity.stage == stage).all()]
        if filtered_ids:
            total_amount = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.id.in_(filtered_ids)).scalar() or 0
        else:
            total_amount = 0

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
    获取销售汇总统计（已集成数据权限过滤）
    """
    # 构建基础查询
    query_leads = db.query(Lead)
    query_opps = db.query(Opportunity)
    query_contracts = db.query(Contract)

    # 应用数据权限过滤
    query_leads = filter_sales_data_by_scope(query_leads, current_user, db, Lead, "owner_id")
    query_opps = filter_sales_data_by_scope(query_opps, current_user, db, Opportunity, "owner_id")
    query_contracts = filter_sales_data_by_scope(query_contracts, current_user, db, Contract, "owner_id")

    # 日期过滤（先应用日期过滤，再获取合同ID用于发票过滤）
    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_opps = query_opps.filter(Opportunity.created_at >= datetime.combine(start_date, datetime.min.time()))
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_opps = query_opps.filter(Opportunity.created_at <= datetime.combine(end_date, datetime.max.time()))
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    # 发票通过合同关联过滤（Invoice 没有 owner_id/created_by 字段）
    # 使用子查询方式，避免加载大量合同ID到内存，同时避免空列表导致的 SQL 错误
    from sqlalchemy import select, func
    
    # 创建合同ID子查询
    contract_ids_subquery = query_contracts.with_entities(Contract.id).subquery()
    
    # 检查是否有可访问的合同
    contract_count = db.query(func.count()).select_from(contract_ids_subquery).scalar() or 0
    
    if contract_count > 0:
        # 使用子查询方式过滤发票
        query_invoices = db.query(Invoice).filter(
            Invoice.contract_id.in_(
                select(contract_ids_subquery.c.id)
            )
        )
    else:
        # 用户没有可访问的合同时，检查是否有全局权限
        from app.core.sales_permissions import get_sales_data_scope
        scope = get_sales_data_scope(current_user, db)
        if scope in ["ALL", "FINANCE_ONLY"]:
            query_invoices = db.query(Invoice)
        else:
            # 返回空结果：使用一个永远为假的条件
            query_invoices = db.query(Invoice).filter(Invoice.id == -1)

    # 对发票应用日期过滤
    if start_date:
        query_invoices = query_invoices.filter(Invoice.created_at >= datetime.combine(start_date, datetime.min.time()))

    if end_date:
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
