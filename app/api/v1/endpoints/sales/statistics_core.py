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

from sqlalchemy import func as sa_func

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
    # Contract 模型使用 sales_owner_id 而非 owner_id
    query_contracts = filter_sales_data_by_scope(
        query_contracts, current_user, db, Contract, "sales_owner_id"
    )

    # 日期过滤
    if start_date:
        query_leads = query_leads.filter(
            Lead.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_opps = query_opps.filter(
            Opportunity.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_quotes = query_quotes.filter(
            Quote.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_contracts = query_contracts.filter(
            Contract.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query_leads = query_leads.filter(
            Lead.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_opps = query_opps.filter(
            Opportunity.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_quotes = query_quotes.filter(
            Quote.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_contracts = query_contracts.filter(
            Contract.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    # 统计各阶段数量
    leads_count = query_leads.count()
    opps_count = query_opps.count()
    quotes_count = query_quotes.count()
    contracts_count = query_contracts.count()

    # 统计金额
    won_opps = query_opps.filter(Opportunity.stage == "WON").all()
    total_opp_amount = sum([float(opp.est_amount or 0) for opp in won_opps])

    signed_contracts = query_contracts.filter(Contract.status == "SIGNED").all()
    total_contract_amount = sum(
        [float(contract.contract_amount or 0) for contract in signed_contracts]
    )

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
                "quote_to_contract": (
                    round(contracts_count / quotes_count * 100, 2) if quotes_count > 0 else 0
                ),
            },
        },
    )


@router.get("/statistics/opportunities-by-stage", response_model=ResponseModel)
def get_opportunities_by_stage(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按阶段统计商机（已集成数据权限过滤）
    """
    stages = ["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "WON", "LOST", "ON_HOLD"]
    result = {}

    from sqlalchemy import func

    # 构建基础查询并应用数据权限过滤
    base_query = db.query(Opportunity)
    base_query = filter_sales_data_by_scope(base_query, current_user, db, Opportunity, "owner_id")

    for stage in stages:
        stage_query = base_query.filter(Opportunity.stage == stage)
        count = stage_query.count()

        # 对于金额统计，需要重新构建查询
        db.query(func.sum(Opportunity.est_amount)).filter(Opportunity.stage == stage)
        # 应用数据权限过滤（需要子查询方式）
        filtered_ids = [opp.id for opp in base_query.filter(Opportunity.stage == stage).all()]
        if filtered_ids:
            total_amount = (
                db.query(func.sum(Opportunity.est_amount))
                .filter(Opportunity.id.in_(filtered_ids))
                .scalar()
                or 0
            )
        else:
            total_amount = 0

        result[stage] = {"count": count, "total_amount": float(total_amount)}

    return ResponseModel(code=200, message="success", data=result)


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
    # Contract 模型使用 sales_owner_id 而非 owner_id
    query_contracts = filter_sales_data_by_scope(
        query_contracts, current_user, db, Contract, "sales_owner_id"
    )

    # 日期过滤（先应用日期过滤，再获取合同ID用于发票过滤）
    if start_date:
        query_leads = query_leads.filter(
            Lead.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_opps = query_opps.filter(
            Opportunity.created_at >= datetime.combine(start_date, datetime.min.time())
        )
        query_contracts = query_contracts.filter(
            Contract.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query_leads = query_leads.filter(
            Lead.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_opps = query_opps.filter(
            Opportunity.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        query_contracts = query_contracts.filter(
            Contract.created_at <= datetime.combine(end_date, datetime.max.time())
        )

    # 发票通过合同关联过滤（Invoice 没有 owner_id/created_by 字段）
    # 使用子查询方式，避免加载大量合同ID到内存，同时避免空列表导致的 SQL 错误
    from sqlalchemy import func, select

    # 创建合同ID子查询
    contract_ids_subquery = query_contracts.with_entities(Contract.id).subquery()

    # 检查是否有可访问的合同
    contract_count = db.query(func.count()).select_from(contract_ids_subquery).scalar() or 0

    if contract_count > 0:
        # 使用子查询方式过滤发票
        query_invoices = db.query(Invoice).filter(
            Invoice.contract_id.in_(select(contract_ids_subquery.c.id))
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
        query_invoices = query_invoices.filter(
            Invoice.created_at >= datetime.combine(start_date, datetime.min.time())
        )

    if end_date:
        query_invoices = query_invoices.filter(
            Invoice.created_at <= datetime.combine(end_date, datetime.max.time())
        )

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
    win_rate = (
        round((won_opportunities / total_opportunities * 100), 2) if total_opportunities > 0 else 0
    )

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
        },
    )


# ==================== 销售统计总览 ====================


@router.get("/statistics/overview", response_model=ResponseModel)
def get_sales_statistics_overview(
    db: Session = Depends(deps.get_db),
    period: Optional[str] = Query("month", description="统计周期: week/month/quarter/year"),
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, description="月份"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    销售统计总览：按时间/产品/客户类型统计，赢单率/输单率
    """
    from calendar import monthrange

    now = datetime.now()
    target_year = year or now.year

    # ---------- 确定时间区间 ----------
    if period == "week":
        # 本周
        weekday = now.weekday()
        start_dt = datetime(now.year, now.month, now.day) - __import__("datetime").timedelta(
            days=weekday
        )
        end_dt = start_dt + __import__("datetime").timedelta(days=7)
    elif period == "quarter":
        q = (now.month - 1) // 3 + 1
        start_dt = datetime(target_year, (q - 1) * 3 + 1, 1)
        end_month = q * 3
        if end_month == 12:
            end_dt = datetime(target_year + 1, 1, 1)
        else:
            end_dt = datetime(target_year, end_month + 1, 1)
    elif period == "year":
        start_dt = datetime(target_year, 1, 1)
        end_dt = datetime(target_year + 1, 1, 1)
    else:
        # month (default)
        m = month or now.month
        start_dt = datetime(target_year, m, 1)
        if m == 12:
            end_dt = datetime(target_year + 1, 1, 1)
        else:
            end_dt = datetime(target_year, m + 1, 1)

    # ---------- 基础查询 + 权限过滤 ----------
    base_opps = db.query(Opportunity).filter(
        Opportunity.created_at >= start_dt,
        Opportunity.created_at < end_dt,
    )
    base_opps = filter_sales_data_by_scope(base_opps, current_user, db, Opportunity, "owner_id")

    base_contracts = db.query(Contract).filter(
        Contract.created_at >= start_dt,
        Contract.created_at < end_dt,
    )
    base_contracts = filter_sales_data_by_scope(
        base_contracts, current_user, db, Contract, "sales_owner_id"
    )

    all_opps = base_opps.all()

    # ---------- 1. 按时间统计 ----------
    time_stats = _build_time_stats(db, current_user, period, target_year, start_dt, end_dt)

    # ---------- 2. 按产品类型统计 ----------
    product_stats = {}
    for opp in all_opps:
        pt = opp.project_type or "未分类"
        if pt not in product_stats:
            product_stats[pt] = {"count": 0, "amount": 0, "won": 0}
        product_stats[pt]["count"] += 1
        product_stats[pt]["amount"] += float(opp.est_amount or 0)
        if opp.stage == "WON":
            product_stats[pt]["won"] += 1
    by_product = [
        {"product_type": k, **v} for k, v in sorted(product_stats.items(), key=lambda x: -x[1]["amount"])
    ]

    # ---------- 3. 按客户类型统计 ----------
    customer_type_stats = {}
    for opp in all_opps:
        cust = opp.customer
        c_type = (cust.industry if cust else None) or "未分类"
        if c_type not in customer_type_stats:
            customer_type_stats[c_type] = {"count": 0, "amount": 0, "won": 0}
        customer_type_stats[c_type]["count"] += 1
        customer_type_stats[c_type]["amount"] += float(opp.est_amount or 0)
        if opp.stage == "WON":
            customer_type_stats[c_type]["won"] += 1
    by_customer_type = [
        {"customer_type": k, **v}
        for k, v in sorted(customer_type_stats.items(), key=lambda x: -x[1]["amount"])
    ]

    # ---------- 4. 赢单率/输单率 ----------
    won_count = sum(1 for o in all_opps if o.stage == "WON")
    lost_count = sum(1 for o in all_opps if o.stage == "LOST")
    closed_count = won_count + lost_count
    win_rate = round(won_count / closed_count * 100, 2) if closed_count > 0 else 0
    loss_rate = round(lost_count / closed_count * 100, 2) if closed_count > 0 else 0
    won_amount = sum(float(o.est_amount or 0) for o in all_opps if o.stage == "WON")
    lost_amount = sum(float(o.est_amount or 0) for o in all_opps if o.stage == "LOST")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": period,
            "date_range": {
                "start": start_dt.strftime("%Y-%m-%d"),
                "end": (end_dt - __import__("datetime").timedelta(seconds=1)).strftime("%Y-%m-%d"),
            },
            "time_series": time_stats,
            "by_product": by_product,
            "by_customer_type": by_customer_type,
            "win_loss": {
                "total_closed": closed_count,
                "won_count": won_count,
                "lost_count": lost_count,
                "win_rate": win_rate,
                "loss_rate": loss_rate,
                "won_amount": won_amount,
                "lost_amount": lost_amount,
            },
        },
    )


def _build_time_stats(
    db: Session,
    current_user: User,
    period: str,
    target_year: int,
    start_dt: datetime,
    end_dt: datetime,
) -> list:
    """按时间段（月/周/季）拆分统计"""
    import datetime as dt_module

    buckets = []

    if period == "year":
        # 按月拆分
        for m in range(1, 13):
            m_start = datetime(target_year, m, 1)
            m_end = datetime(target_year, m + 1, 1) if m < 12 else datetime(target_year + 1, 1, 1)
            buckets.append((f"{m}月", m_start, m_end))
    elif period == "quarter":
        q = (start_dt.month - 1) // 3 + 1
        for m_offset in range(3):
            m = (q - 1) * 3 + 1 + m_offset
            m_start = datetime(target_year, m, 1)
            m_end = (
                datetime(target_year, m + 1, 1)
                if m < 12
                else datetime(target_year + 1, 1, 1)
            )
            buckets.append((f"{m}月", m_start, m_end))
    elif period == "week":
        for d in range(7):
            day = start_dt + dt_module.timedelta(days=d)
            day_end = day + dt_module.timedelta(days=1)
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            buckets.append((weekday_names[d], day, day_end))
    else:
        # month - 按周拆分
        current = start_dt
        week_num = 1
        while current < end_dt:
            w_end = min(current + dt_module.timedelta(days=7), end_dt)
            buckets.append((f"第{week_num}周", current, w_end))
            current = w_end
            week_num += 1

    result = []
    for label, b_start, b_end in buckets:
        query = db.query(Opportunity).filter(
            Opportunity.created_at >= b_start,
            Opportunity.created_at < b_end,
        )
        query = filter_sales_data_by_scope(query, current_user, db, Opportunity, "owner_id")

        total = query.count()
        won = query.filter(Opportunity.stage == "WON").count()
        amount = float(
            query.with_entities(sa_func.coalesce(sa_func.sum(Opportunity.est_amount), 0)).scalar()
            or 0
        )
        won_amount = float(
            query.filter(Opportunity.stage == "WON")
            .with_entities(sa_func.coalesce(sa_func.sum(Opportunity.est_amount), 0))
            .scalar()
            or 0
        )

        result.append(
            {
                "label": label,
                "opp_count": total,
                "won_count": won,
                "total_amount": amount,
                "won_amount": won_amount,
            }
        )

    return result
