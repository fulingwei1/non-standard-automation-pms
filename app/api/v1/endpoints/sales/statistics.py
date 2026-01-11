# -*- coding: utf-8 -*-
"""
销售统计与报表 API endpoints

包含销售漏斗统计、商机按阶段统计、收入预测、销售预测、
预测准确率评估、汇总统计以及各类报表（销售漏斗报表、
赢输分析、销售业绩、客户贡献、O2C管道）。
"""

from typing import Any, Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api import deps
from app.core import security
from app.models.user import User
from app.models.sales import (
    Lead, Opportunity, Quote, Contract, Invoice
)
from app.schemas.common import ResponseModel
from app.services.sales_prediction_service import SalesPredictionService

router = APIRouter()


# ==================== 统计端点 ====================


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

    for stage in stages:
        count = db.query(Opportunity).filter(Opportunity.stage == stage).count()
        total_amount = db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage).scalar() or 0
        result[stage] = {
            "count": count,
            "total_amount": float(total_amount)
        }

    return ResponseModel(code=200, message="success", data=result)


@router.get("/statistics/revenue-forecast", response_model=ResponseModel)
def get_revenue_forecast(
    db: Session = Depends(deps.get_db),
    months: int = Query(3, ge=1, le=12, description="预测月数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    收入预测（基于已签订合同和进行中的商机）
    """
    from datetime import timedelta
    from calendar import monthrange

    today = date.today()
    forecast = []

    for i in range(months):
        forecast_date = today + timedelta(days=30 * (i + 1))
        month_start = forecast_date.replace(day=1)
        _, last_day = monthrange(forecast_date.year, forecast_date.month)
        month_end = forecast_date.replace(day=last_day)

        # 统计该月预计签约的合同金额（基于商机预计金额）
        opps_in_month = (
            db.query(Opportunity)
            .filter(Opportunity.stage.in_(["PROPOSAL", "NEGOTIATION"]))
            .all()
        )

        # 简化处理：假设进行中的商机在接下来几个月平均分布
        estimated_revenue = sum([float(opp.est_amount or 0) for opp in opps_in_month]) / months

        forecast.append({
            "month": forecast_date.strftime("%Y-%m"),
            "estimated_revenue": round(estimated_revenue, 2)
        })

    return ResponseModel(code=200, message="success", data={"forecast": forecast})


@router.get("/statistics/prediction", response_model=ResponseModel)
def get_sales_prediction(
    *,
    db: Session = Depends(deps.get_db),
    days: int = Query(90, ge=30, le=365, description="预测天数（30/60/90）"),
    method: str = Query("moving_average", description="预测方法：moving_average/exponential_smoothing"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.3: 销售预测增强
    使用移动平均法或指数平滑法进行收入预测
    """
    service = SalesPredictionService(db)
    prediction = service.predict_revenue(
        days=days,
        method=method,
        customer_id=customer_id,
        owner_id=owner_id,
    )

    return ResponseModel(
        code=200,
        message="success",
        data=prediction
    )


@router.get("/statistics/prediction/accuracy", response_model=ResponseModel)
def get_prediction_accuracy(
    *,
    db: Session = Depends(deps.get_db),
    days_back: int = Query(90, ge=30, le=365, description="评估时间段（天数）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 6.3: 预测准确度评估
    对比历史预测值和实际值
    """
    service = SalesPredictionService(db)
    accuracy = service.evaluate_prediction_accuracy(days_back=days_back)

    return ResponseModel(
        code=200,
        message="success",
        data=accuracy
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


# ==================== 报表端点 ====================


@router.get("/reports/sales-funnel", response_model=ResponseModel)
def get_sales_funnel_report(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售漏斗报表
    """
    # 复用已有的统计逻辑
    return get_sales_funnel(db, start_date, end_date, current_user)


@router.get("/reports/win-loss", response_model=ResponseModel)
def get_win_loss_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    赢单/丢单分析
    """
    query = db.query(Opportunity)

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
    销售业绩统计
    """
    query_opps = db.query(Opportunity)
    query_contracts = db.query(Contract)
    query_invoices = db.query(Invoice)

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
        query_contracts = query_contracts.filter(Contract.owner_id == owner_id)

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
    客户贡献分析
    """
    query_contracts = db.query(Contract).filter(Contract.status == "SIGNED")

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
    O2C流程全链路统计
    """
    from datetime import date as date_type
    today = date_type.today()

    # 线索统计
    query_leads = db.query(Lead)
    if start_date:
        query_leads = query_leads.filter(Lead.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_leads = query_leads.filter(Lead.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_leads = query_leads.count()
    converted_leads = query_leads.filter(Lead.status == "CONVERTED").count()

    # 商机统计
    query_opps = db.query(Opportunity)
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
    if start_date:
        query_quotes = query_quotes.filter(Quote.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_quotes = query_quotes.filter(Quote.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_quotes = query_quotes.count()
    approved_quotes = query_quotes.filter(Quote.status == "APPROVED").all()
    approved_amount = sum([float(q.total_price or 0) for q in approved_quotes])

    # 合同统计
    query_contracts = db.query(Contract)
    if start_date:
        query_contracts = query_contracts.filter(Contract.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query_contracts = query_contracts.filter(Contract.created_at <= datetime.combine(end_date, datetime.max.time()))

    total_contracts = query_contracts.count()
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    signed_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])

    # 发票统计
    query_invoices = db.query(Invoice)
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
