# -*- coding: utf-8 -*-
"""
销售统计 - 报表功能

包含销售漏斗报表、赢输分析、销售业绩、客户贡献、O2C管道等报表
已集成数据权限过滤：不同角色看到不同范围的统计数据
"""

from datetime import date
from datetime import date as date_type
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from sqlalchemy import func as sa_func

from app.api import deps
from app.core import security
from app.core.sales_permissions import (
    filter_sales_data_by_scope,
    filter_sales_finance_data_by_scope,
)
from app.models.organization import Department
from app.models.sales import Contract, Invoice, Lead, Opportunity, Quote, SalesTarget
from app.models.user import User
from app.schemas.common import ResponseModel

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
        query = query.filter(
            Opportunity.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query = query.filter(
            Opportunity.created_at <= datetime.combine(end_date, datetime.max.time())
        )

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
            "won": {"count": won_count, "amount": won_amount},
            "lost": {"count": lost_count, "amount": lost_amount},
            "win_rate": win_rate,
            "total_count": total_count,
        },
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
    query_contracts = filter_sales_data_by_scope(
        query_contracts, current_user, db, Contract, "owner_id"
    )
    query_invoices = filter_sales_finance_data_by_scope(
        query_invoices, current_user, db, Invoice, "created_by"
    )

    if start_date:
        query_opps = query_opps.filter(
            Opportunity.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_contracts = query_contracts.filter(
            Contract.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_invoices = query_invoices.filter(
            Invoice.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query_opps = query_opps.filter(
            Opportunity.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_contracts = query_contracts.filter(
            Contract.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_invoices = query_invoices.filter(
            Invoice.created_at <= datetime.combine(end_date, datetime.max.time())
        )

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
            "total_invoice_amount": total_invoice_amount,
        },
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
    query_contracts = filter_sales_data_by_scope(
        query_contracts, current_user, db, Contract, "owner_id"
    )

    if start_date:
        query_contracts = query_contracts.filter(
            Contract.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query_contracts = query_contracts.filter(
            Contract.created_at <= datetime.combine(end_date, datetime.max.time())
        )

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
                "total_amount": 0,
            }
        customer_stats[customer_id]["contract_count"] += 1
        customer_stats[customer_id]["total_amount"] += float(contract.contract_amount or 0)

    # 排序并取前N名
    sorted_customers = sorted(
        customer_stats.values(), key=lambda x: x["total_amount"], reverse=True
    )[:top_n]

    return ResponseModel(
        code=200,
        message="success",
        data={"customers": sorted_customers, "total_customers": len(customer_stats)},
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
        query_leads = query_leads.filter(
            Lead.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query_leads = query_leads.filter(
            Lead.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    total_leads = query_leads.count()
    converted_leads = query_leads.filter(Lead.status == "CONVERTED").count()

    # 商机统计
    query_opps = db.query(Opportunity)
    query_opps = filter_sales_data_by_scope(query_opps, current_user, db, Opportunity, "owner_id")
    if start_date:
        query_opps = query_opps.filter(
            Opportunity.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query_opps = query_opps.filter(
            Opportunity.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    total_opps = query_opps.count()
    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    won_count = len(won_opps)
    won_amount = sum([float(opp.est_amount or 0) for opp in won_opps])

    # 报价统计
    query_quotes = db.query(Quote)
    query_quotes = filter_sales_data_by_scope(query_quotes, current_user, db, Quote, "owner_id")
    if start_date:
        query_quotes = query_quotes.filter(
            Quote.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query_quotes = query_quotes.filter(
            Quote.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    total_quotes = query_quotes.count()
    approved_quotes = query_quotes.filter(Quote.status == "APPROVED").all()
    approved_amount = sum([float(q.total_price or 0) for q in approved_quotes])

    # 合同统计
    query_contracts = db.query(Contract)
    query_contracts = filter_sales_data_by_scope(
        query_contracts, current_user, db, Contract, "owner_id"
    )
    if start_date:
        query_contracts = query_contracts.filter(
            Contract.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query_contracts = query_contracts.filter(
            Contract.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    total_contracts = query_contracts.count()
    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    signed_amount = sum([float(c.contract_amount or 0) for c in signed_contracts])

    # 发票统计（使用财务数据权限）
    query_invoices = db.query(Invoice)
    query_invoices = filter_sales_finance_data_by_scope(
        query_invoices, current_user, db, Invoice, "created_by"
    )
    if start_date:
        query_invoices = query_invoices.filter(
            Invoice.created_at >= datetime.combine(start_date, datetime.min.time())
        )
    if end_date:
        query_invoices = query_invoices.filter(
            Invoice.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    total_invoices = query_invoices.filter(Invoice.status == "ISSUED").count()
    issued_invoices = query_invoices.filter(Invoice.status == "ISSUED").all()
    issued_amount = sum([float(inv.total_amount or inv.amount or 0) for inv in issued_invoices])

    # 收款统计
    paid_invoices = query_invoices.filter(Invoice.payment_status == "PAID").all()
    paid_amount = sum([float(inv.paid_amount or 0) for inv in paid_invoices])

    partial_invoices = query_invoices.filter(Invoice.payment_status == "PARTIAL").all()
    partial_amount = sum([float(inv.paid_amount or 0) for inv in partial_invoices])

    pending_invoices = query_invoices.filter(Invoice.payment_status == "PENDING").all()
    pending_amount = sum(
        [
            float(inv.total_amount or inv.amount or 0) - float(inv.paid_amount or 0)
            for inv in pending_invoices
        ]
    )

    # 逾期统计
    overdue_invoices = query_invoices.filter(
        Invoice.status == "ISSUED",
        Invoice.due_date < today,
        Invoice.payment_status.in_(["PENDING", "PARTIAL"]),
    ).all()
    overdue_amount = sum(
        [
            float(inv.total_amount or inv.amount or 0) - float(inv.paid_amount or 0)
            for inv in overdue_invoices
        ]
    )

    # 计算转化率
    conversion_rate = round(converted_leads / total_leads * 100, 2) if total_leads > 0 else 0
    win_rate = round(won_count / total_opps * 100, 2) if total_opps > 0 else 0
    quote_to_contract_rate = (
        round(total_contracts / total_quotes * 100, 2) if total_quotes > 0 else 0
    )
    contract_to_invoice_rate = (
        round(total_invoices / len(signed_contracts) * 100, 2) if signed_contracts else 0
    )
    collection_rate = round(paid_amount / issued_amount * 100, 2) if issued_amount > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "leads": {
                "total": total_leads,
                "converted": converted_leads,
                "conversion_rate": conversion_rate,
            },
            "opportunities": {
                "total": total_opps,
                "won": won_count,
                "won_amount": won_amount,
                "win_rate": win_rate,
            },
            "quotes": {
                "total": total_quotes,
                "approved": len(approved_quotes),
                "approved_amount": approved_amount,
            },
            "contracts": {
                "total": total_contracts,
                "signed": len(signed_contracts),
                "signed_amount": signed_amount,
                "quote_to_contract_rate": quote_to_contract_rate,
            },
            "invoices": {
                "total": total_invoices,
                "issued_amount": issued_amount,
                "contract_to_invoice_rate": contract_to_invoice_rate,
            },
            "receivables": {
                "paid_amount": paid_amount,
                "partial_amount": partial_amount,
                "pending_amount": pending_amount,
                "overdue_count": len(overdue_invoices),
                "overdue_amount": overdue_amount,
                "collection_rate": collection_rate,
            },
            "pipeline_health": {
                "lead_to_opp_rate": (
                    round(total_opps / total_leads * 100, 2) if total_leads > 0 else 0
                ),
                "opp_to_quote_rate": (
                    round(total_quotes / total_opps * 100, 2) if total_opps > 0 else 0
                ),
                "quote_to_contract_rate": quote_to_contract_rate,
                "contract_to_invoice_rate": contract_to_invoice_rate,
                "collection_rate": collection_rate,
            },
        },
    )


# ==================== 综合业绩报表 ====================


@router.get("/reports/performance", response_model=ResponseModel)
def get_performance_report(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="用户ID（查看个人）"),
    department_id: Optional[int] = Query(None, description="部门ID（查看团队）"),
    report_type: str = Query("personal", description="报表类型: personal/team/forecast"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    综合销售业绩报表

    - personal: 个人业绩报表（赢单、合同、回款、目标完成率）
    - team: 团队业绩报表（部门/团队维度汇总 + 成员明细）
    - forecast: 销售预测报表（管道加权预测 vs 实际）
    """
    # 默认时间范围：当年
    now = datetime.now()
    if not start_date:
        start_date = date(now.year, 1, 1)
    if not end_date:
        end_date = date(now.year, 12, 31)

    dt_start = datetime.combine(start_date, datetime.min.time())
    dt_end = datetime.combine(end_date, datetime.max.time())

    if report_type == "team":
        data = _team_performance(db, current_user, dt_start, dt_end, department_id)
    elif report_type == "forecast":
        data = _forecast_report(db, current_user, dt_start, dt_end)
    else:
        data = _personal_performance(db, current_user, dt_start, dt_end, user_id)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "report_type": report_type,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            **data,
        },
    )


def _personal_performance(
    db: Session,
    current_user: User,
    dt_start: datetime,
    dt_end: datetime,
    user_id: Optional[int],
) -> dict:
    """个人业绩报表"""
    target_uid = user_id or current_user.id

    # 商机
    opps = (
        db.query(Opportunity)
        .filter(
            Opportunity.owner_id == target_uid,
            Opportunity.created_at >= dt_start,
            Opportunity.created_at <= dt_end,
        )
        .all()
    )
    total_opps = len(opps)
    won_opps = [o for o in opps if o.stage == "WON"]
    lost_opps = [o for o in opps if o.stage == "LOST"]
    won_amount = sum(float(o.est_amount or 0) for o in won_opps)
    lost_amount = sum(float(o.est_amount or 0) for o in lost_opps)
    pipeline_amount = sum(
        float(o.est_amount or 0)
        for o in opps
        if o.stage not in ("WON", "LOST", "ON_HOLD")
    )

    # 合同
    contracts = (
        db.query(Contract)
        .filter(
            Contract.sales_owner_id == target_uid,
            Contract.created_at >= dt_start,
            Contract.created_at <= dt_end,
        )
        .all()
    )
    signed = [c for c in contracts if c.status == "signed"]
    contract_amount = sum(float(c.total_amount or 0) for c in signed)
    received = sum(float(c.received_amount or 0) for c in signed)

    # 目标完成率
    year_str = str(dt_start.year)
    target_row = (
        db.query(SalesTarget)
        .filter(
            SalesTarget.user_id == target_uid,
            SalesTarget.target_scope == "PERSONAL",
            SalesTarget.target_type == "CONTRACT_AMOUNT",
            SalesTarget.target_period == "YEARLY",
            SalesTarget.period_value == year_str,
            SalesTarget.status == "ACTIVE",
        )
        .first()
    )
    target_val = float(target_row.target_value) if target_row else 0
    completion_rate = round(won_amount / target_val * 100, 1) if target_val > 0 else 0

    # 用户信息
    user = db.query(User).filter(User.id == target_uid).first()

    return {
        "user": {
            "id": target_uid,
            "name": (user.real_name or user.username) if user else None,
        },
        "opportunities": {
            "total": total_opps,
            "won": len(won_opps),
            "lost": len(lost_opps),
            "in_pipeline": total_opps - len(won_opps) - len(lost_opps),
            "won_amount": won_amount,
            "lost_amount": lost_amount,
            "pipeline_amount": pipeline_amount,
            "win_rate": (
                round(len(won_opps) / (len(won_opps) + len(lost_opps)) * 100, 1)
                if (len(won_opps) + len(lost_opps)) > 0
                else 0
            ),
        },
        "contracts": {
            "total": len(contracts),
            "signed": len(signed),
            "contract_amount": contract_amount,
            "received_amount": received,
            "collection_rate": (
                round(received / contract_amount * 100, 1) if contract_amount > 0 else 0
            ),
        },
        "target": {
            "target_value": target_val,
            "achieved": won_amount,
            "completion_rate": completion_rate,
            "gap": round(target_val - won_amount, 2),
        },
    }


def _team_performance(
    db: Session,
    current_user: User,
    dt_start: datetime,
    dt_end: datetime,
    department_id: Optional[int],
) -> dict:
    """团队业绩报表"""
    # 获取部门信息
    dept = None
    if department_id:
        dept = db.query(Department).filter(Department.id == department_id).first()

    # 查询范围内所有赢单，按 owner 分组
    query = db.query(Opportunity).filter(
        Opportunity.stage == "WON",
        Opportunity.created_at >= dt_start,
        Opportunity.created_at <= dt_end,
    )
    query = filter_sales_data_by_scope(query, current_user, db, Opportunity, "owner_id")

    won_opps = query.all()

    # 按负责人汇总
    member_map = {}
    for opp in won_opps:
        uid = opp.owner_id
        if uid not in member_map:
            member_map[uid] = {"won_count": 0, "won_amount": 0}
        member_map[uid]["won_count"] += 1
        member_map[uid]["won_amount"] += float(opp.est_amount or 0)

    # 构建成员明细
    members = []
    for uid, stats in sorted(member_map.items(), key=lambda x: -x[1]["won_amount"]):
        user = db.query(User).filter(User.id == uid).first()
        if not user:
            continue

        # 个人合同
        signed_contracts = (
            db.query(Contract)
            .filter(
                Contract.sales_owner_id == uid,
                Contract.status == "signed",
                Contract.created_at >= dt_start,
                Contract.created_at <= dt_end,
            )
            .all()
        )
        contract_amount = sum(float(c.total_amount or 0) for c in signed_contracts)

        # 个人目标
        year_str = str(dt_start.year)
        t = (
            db.query(SalesTarget)
            .filter(
                SalesTarget.user_id == uid,
                SalesTarget.target_scope == "PERSONAL",
                SalesTarget.target_type == "CONTRACT_AMOUNT",
                SalesTarget.target_period == "YEARLY",
                SalesTarget.period_value == year_str,
                SalesTarget.status == "ACTIVE",
            )
            .first()
        )
        t_val = float(t.target_value) if t else 0
        completion = round(stats["won_amount"] / t_val * 100, 1) if t_val > 0 else 0

        members.append(
            {
                "user_id": uid,
                "name": user.real_name or user.username,
                "won_count": stats["won_count"],
                "won_amount": stats["won_amount"],
                "contract_amount": contract_amount,
                "target": t_val,
                "completion_rate": completion,
            }
        )

    # 汇总
    total_won = sum(m["won_amount"] for m in members)
    total_contracts = sum(m["contract_amount"] for m in members)

    return {
        "department": {
            "id": department_id,
            "name": dept.dept_name if dept else "全部",
        },
        "summary": {
            "member_count": len(members),
            "total_won_amount": total_won,
            "total_contract_amount": total_contracts,
            "avg_per_member": round(total_won / len(members), 2) if members else 0,
        },
        "members": members,
    }


def _forecast_report(
    db: Session,
    current_user: User,
    dt_start: datetime,
    dt_end: datetime,
) -> dict:
    """销售预测报表"""
    base_query = db.query(Opportunity).filter(
        Opportunity.created_at >= dt_start,
        Opportunity.created_at <= dt_end,
    )
    base_query = filter_sales_data_by_scope(base_query, current_user, db, Opportunity, "owner_id")

    # 已赢单
    won = base_query.filter(Opportunity.stage == "WON").all()
    actual_amount = sum(float(o.est_amount or 0) for o in won)

    # 管道中各阶段加权预测
    active_stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION"]
    stage_names = {
        "DISCOVERY": "初步接触",
        "QUALIFICATION": "需求确认",
        "PROPOSAL": "方案报价",
        "NEGOTIATION": "商务谈判",
    }

    stage_forecasts = []
    total_weighted = 0
    for stage in active_stages:
        stage_opps = base_query.filter(Opportunity.stage == stage).all()
        raw = sum(float(o.est_amount or 0) for o in stage_opps)
        weighted = sum(
            float(o.est_amount or 0) * (o.probability or 0) / 100 for o in stage_opps
        )
        total_weighted += weighted
        stage_forecasts.append(
            {
                "stage": stage_names.get(stage, stage),
                "count": len(stage_opps),
                "raw_amount": raw,
                "weighted_amount": round(weighted, 2),
            }
        )

    forecast_total = actual_amount + total_weighted

    # 按月拆分预测
    import datetime as dt_module

    monthly_forecast = []
    current = dt_start
    while current < dt_end:
        m = current.month
        y = current.year
        m_end = datetime(y, m + 1, 1) if m < 12 else datetime(y + 1, 1, 1)

        m_won = (
            base_query.filter(
                Opportunity.stage == "WON",
                Opportunity.created_at >= current,
                Opportunity.created_at < m_end,
            )
            .with_entities(sa_func.coalesce(sa_func.sum(Opportunity.est_amount), 0))
            .scalar()
        )

        m_pipeline = base_query.filter(
            Opportunity.stage.in_(active_stages),
            Opportunity.expected_close_date >= current.date(),
            Opportunity.expected_close_date < m_end.date(),
        ).all()
        m_weighted = sum(
            float(o.est_amount or 0) * (o.probability or 0) / 100 for o in m_pipeline
        )

        monthly_forecast.append(
            {
                "month": f"{y}-{m:02d}",
                "actual": float(m_won or 0),
                "forecast": round(float(m_won or 0) + m_weighted, 2),
            }
        )

        current = m_end

    return {
        "actual_won": actual_amount,
        "pipeline_weighted": round(total_weighted, 2),
        "forecast_total": round(forecast_total, 2),
        "by_stage": stage_forecasts,
        "monthly": monthly_forecast,
    }
