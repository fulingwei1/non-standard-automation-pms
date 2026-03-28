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
