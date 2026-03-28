# -*- coding: utf-8 -*-
"""
销售全链路转化率分析

功能：
1. 线索→商机→报价→合同 每一步转化率
2. 每个销售人员的转化率
"""

from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import Contract, Lead, Opportunity, Quote
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/conversion/full-pipeline", response_model=ResponseModel, summary="全链路转化率")
def get_full_pipeline_conversion(
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    线索→商机→报价→合同 每一步转化率
    
    返回：
    - 每个阶段的数量
    - 每一步的转化率
    - 全链路转化率（线索→合同）
    """
    # 时间范围
    now = datetime.now()
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = now - timedelta(days=365)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end = now
    
    # 统计各阶段数量
    leads_count = db.query(func.count(Lead.id)).filter(
        Lead.created_at >= start, Lead.created_at <= end
    ).scalar() or 0
    
    opportunities_count = db.query(func.count(Opportunity.id)).filter(
        Opportunity.created_at >= start, Opportunity.created_at <= end
    ).scalar() or 0
    
    quotes_count = db.query(func.count(Quote.id)).filter(
        Quote.created_at >= start, Quote.created_at <= end
    ).scalar() or 0
    
    contracts_count = db.query(func.count(Contract.id)).filter(
        Contract.created_at >= start, Contract.created_at <= end
    ).scalar() or 0
    
    # 计算转化率
    lead_to_opp = round(opportunities_count / leads_count * 100, 1) if leads_count else 0
    opp_to_quote = round(quotes_count / opportunities_count * 100, 1) if opportunities_count else 0
    quote_to_contract = round(contracts_count / quotes_count * 100, 1) if quotes_count else 0
    lead_to_contract = round(contracts_count / leads_count * 100, 1) if leads_count else 0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start.date()), "end": str(end.date())},
            "stages": [
                {"stage": "线索", "count": leads_count, "icon": "📋"},
                {"stage": "商机", "count": opportunities_count, "icon": "💡"},
                {"stage": "报价", "count": quotes_count, "icon": "💰"},
                {"stage": "合同", "count": contracts_count, "icon": "📄"},
            ],
            "conversions": [
                {"from": "线索", "to": "商机", "rate": lead_to_opp, "count_from": leads_count, "count_to": opportunities_count},
                {"from": "商机", "to": "报价", "rate": opp_to_quote, "count_from": opportunities_count, "count_to": quotes_count},
                {"from": "报价", "to": "合同", "rate": quote_to_contract, "count_from": quotes_count, "count_to": contracts_count},
            ],
            "overall": {
                "from": "线索",
                "to": "合同",
                "rate": lead_to_contract,
                "count_from": leads_count,
                "count_to": contracts_count,
            },
        },
    )


@router.get("/conversion/by-person", response_model=ResponseModel, summary="每个人的转化率")
def get_conversion_by_person(
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    每个销售人员的转化率统计
    
    返回：
    - 每个人的线索数/商机数/报价数/合同数
    - 每一步转化率
    - 全链路转化率
    - 排名
    """
    now = datetime.now()
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start = now - timedelta(days=365)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end = now
    
    # 按负责人统计线索
    lead_stats = dict(
        db.query(Lead.owner_id, func.count(Lead.id))
        .filter(Lead.created_at >= start, Lead.created_at <= end)
        .group_by(Lead.owner_id)
        .all()
    )
    
    # 按负责人统计商机
    opp_stats = dict(
        db.query(Opportunity.owner_id, func.count(Opportunity.id))
        .filter(Opportunity.created_at >= start, Opportunity.created_at <= end)
        .group_by(Opportunity.owner_id)
        .all()
    )
    
    # 按负责人统计报价
    quote_stats = dict(
        db.query(Quote.owner_id, func.count(Quote.id))
        .filter(Quote.created_at >= start, Quote.created_at <= end)
        .group_by(Quote.owner_id)
        .all()
    )
    
    # 按负责人统计合同
    contract_stats = dict(
        db.query(Contract.owner_id, func.count(Contract.id))
        .filter(Contract.created_at >= start, Contract.created_at <= end)
        .group_by(Contract.owner_id)
        .all()
    )
    
    # 合并所有负责人
    all_owners = set(lead_stats.keys()) | set(opp_stats.keys()) | set(quote_stats.keys()) | set(contract_stats.keys())
    
    # 查询用户名
    users = {u.id: u.username for u in db.query(User).filter(User.id.in_(all_owners)).all()}
    
    # 构建每个人的数据
    person_data = []
    for owner_id in all_owners:
        if not owner_id:
            continue
        
        leads = lead_stats.get(owner_id, 0)
        opps = opp_stats.get(owner_id, 0)
        quotes = quote_stats.get(owner_id, 0)
        contracts = contract_stats.get(owner_id, 0)
        
        lead_to_opp = round(opps / leads * 100, 1) if leads else 0
        opp_to_quote = round(quotes / opps * 100, 1) if opps else 0
        quote_to_contract = round(contracts / quotes * 100, 1) if quotes else 0
        overall = round(contracts / leads * 100, 1) if leads else 0
        
        person_data.append({
            "user_id": owner_id,
            "user_name": users.get(owner_id, f"用户{owner_id}"),
            "leads": leads,
            "opportunities": opps,
            "quotes": quotes,
            "contracts": contracts,
            "lead_to_opportunity": lead_to_opp,
            "opportunity_to_quote": opp_to_quote,
            "quote_to_contract": quote_to_contract,
            "overall_conversion": overall,
        })
    
    # 按全链路转化率排名
    person_data.sort(key=lambda x: x["overall_conversion"], reverse=True)
    
    # 添加排名
    for i, p in enumerate(person_data, 1):
        p["rank"] = i
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start.date()), "end": str(end.date())},
            "total_persons": len(person_data),
            "persons": person_data,
            "avg_overall_conversion": round(sum(p["overall_conversion"] for p in person_data) / len(person_data), 1) if person_data else 0,
        },
    )



@router.get("/conversion/trend", response_model=ResponseModel, summary="转化率趋势（按月）")
def get_conversion_trend(
    db: Session = Depends(deps.get_db),
    months: int = Query(6, ge=1, le=24, description="统计月数"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    按月统计转化率趋势
    
    返回每个月的：线索数/商机数/报价数/合同数 + 各步骤转化率
    """
    from dateutil.relativedelta import relativedelta
    
    now = datetime.now()
    monthly_data = []
    
    for i in range(months - 1, -1, -1):
        month_start = (now - relativedelta(months=i)).replace(day=1, hour=0, minute=0, second=0)
        month_end = (month_start + relativedelta(months=1)) - timedelta(seconds=1)
        month_label = month_start.strftime("%Y-%m")
        
        leads = db.query(func.count(Lead.id)).filter(Lead.created_at >= month_start, Lead.created_at <= month_end).scalar() or 0
        opps = db.query(func.count(Opportunity.id)).filter(Opportunity.created_at >= month_start, Opportunity.created_at <= month_end).scalar() or 0
        quotes = db.query(func.count(Quote.id)).filter(Quote.created_at >= month_start, Quote.created_at <= month_end).scalar() or 0
        contracts = db.query(func.count(Contract.id)).filter(Contract.created_at >= month_start, Contract.created_at <= month_end).scalar() or 0
        
        monthly_data.append({
            "month": month_label,
            "leads": leads,
            "opportunities": opps,
            "quotes": quotes,
            "contracts": contracts,
            "lead_to_opportunity": round(opps / leads * 100, 1) if leads else 0,
            "opportunity_to_quote": round(quotes / opps * 100, 1) if opps else 0,
            "quote_to_contract": round(contracts / quotes * 100, 1) if quotes else 0,
            "overall": round(contracts / leads * 100, 1) if leads else 0,
        })
    
    # 计算趋势方向
    if len(monthly_data) >= 2:
        recent = monthly_data[-1]["overall"]
        previous = monthly_data[-2]["overall"]
        trend = "UP" if recent > previous else ("DOWN" if recent < previous else "STABLE")
        trend_delta = round(recent - previous, 1)
    else:
        trend = "STABLE"
        trend_delta = 0
    
    return ResponseModel(code=200, message="success", data={
        "months": monthly_data,
        "trend": trend,
        "trend_delta": trend_delta,
    })


@router.get("/conversion/bottleneck", response_model=ResponseModel, summary="转化率瓶颈分析")
def get_conversion_bottleneck(
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    识别转化率最低的环节，给出优化建议
    """
    now = datetime.now()
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else now - timedelta(days=365)
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else now
    
    leads = db.query(func.count(Lead.id)).filter(Lead.created_at >= start, Lead.created_at <= end).scalar() or 0
    opps = db.query(func.count(Opportunity.id)).filter(Opportunity.created_at >= start, Opportunity.created_at <= end).scalar() or 0
    quotes = db.query(func.count(Quote.id)).filter(Quote.created_at >= start, Quote.created_at <= end).scalar() or 0
    contracts = db.query(func.count(Contract.id)).filter(Contract.created_at >= start, Contract.created_at <= end).scalar() or 0
    
    steps = [
        {"step": "线索→商机", "rate": round(opps / leads * 100, 1) if leads else 0, "benchmark": 60, "from_count": leads, "to_count": opps},
        {"step": "商机→报价", "rate": round(quotes / opps * 100, 1) if opps else 0, "benchmark": 50, "from_count": opps, "to_count": quotes},
        {"step": "报价→合同", "rate": round(contracts / quotes * 100, 1) if quotes else 0, "benchmark": 40, "from_count": quotes, "to_count": contracts},
    ]
    
    # 找出瓶颈
    bottleneck = min(steps, key=lambda x: x["rate"]) if steps else None
    
    # 生成建议
    suggestions = []
    for step in steps:
        if step["rate"] < step["benchmark"]:
            gap = round(step["benchmark"] - step["rate"], 1)
            if step["step"] == "线索→商机":
                suggestions.append({
                    "step": step["step"],
                    "current_rate": step["rate"],
                    "benchmark": step["benchmark"],
                    "gap": gap,
                    "suggestions": [
                        "提高线索质量筛选标准",
                        "加快线索跟进速度（48 小时内首次联系）",
                        "优化客户画像匹配度",
                        "增加行业活动/展会获客渠道",
                    ],
                })
            elif step["step"] == "商机→报价":
                suggestions.append({
                    "step": step["step"],
                    "current_rate": step["rate"],
                    "benchmark": step["benchmark"],
                    "gap": gap,
                    "suggestions": [
                        "缩短方案制作周期",
                        "提供更有竞争力的报价",
                        "加强售前技术支持",
                        "建立标准化报价模板",
                    ],
                })
            elif step["step"] == "报价→合同":
                suggestions.append({
                    "step": step["step"],
                    "current_rate": step["rate"],
                    "benchmark": step["benchmark"],
                    "gap": gap,
                    "suggestions": [
                        "分析丢单原因（价格/技术/交期）",
                        "加强商务谈判能力",
                        "提供灵活的付款方式",
                        "展示成功案例和客户评价",
                    ],
                })
    
    return ResponseModel(code=200, message="success", data={
        "steps": steps,
        "bottleneck": bottleneck,
        "suggestions": suggestions,
        "overall_rate": round(contracts / leads * 100, 1) if leads else 0,
    })


@router.get("/conversion/lost-analysis", response_model=ResponseModel, summary="丢单原因分析")
def get_lost_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """分析丢单原因"""
    now = datetime.now()
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else now - timedelta(days=365)
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else now
    
    # 查询丢单商机
    lost_opps = db.query(Opportunity).filter(
        Opportunity.stage == "LOST",
        Opportunity.created_at >= start,
        Opportunity.created_at <= end,
    ).all()
    
    # 按丢单原因分类
    reasons = {}
    for opp in lost_opps:
        reason = getattr(opp, 'loss_reason', '未知') or '未知'
        if reason not in reasons:
            reasons[reason] = {"count": 0, "amount": 0}
        reasons[reason]["count"] += 1
        reasons[reason]["amount"] += float(opp.est_amount or 0)
    
    # 按人统计丢单
    lost_by_person = {}
    for opp in lost_opps:
        owner = opp.owner_id
        if owner not in lost_by_person:
            lost_by_person[owner] = {"count": 0, "amount": 0}
        lost_by_person[owner]["count"] += 1
        lost_by_person[owner]["amount"] += float(opp.est_amount or 0)
    
    # 查询用户名
    user_ids = list(lost_by_person.keys())
    users = {u.id: u.username for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    
    return ResponseModel(code=200, message="success", data={
        "total_lost": len(lost_opps),
        "total_lost_amount": sum(float(o.est_amount or 0) for o in lost_opps),
        "by_reason": [{"reason": k, "count": v["count"], "amount": v["amount"]} for k, v in sorted(reasons.items(), key=lambda x: x[1]["count"], reverse=True)],
        "by_person": [{"user_id": k, "user_name": users.get(k, f"用户{k}"), "count": v["count"], "amount": v["amount"]} for k, v in sorted(lost_by_person.items(), key=lambda x: x[1]["count"], reverse=True)],
    })
