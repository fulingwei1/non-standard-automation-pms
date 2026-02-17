# -*- coding: utf-8 -*-
"""
投标管理 - 自动生成
从 presale.py 拆分
"""

# -*- coding: utf-8 -*-
"""
售前技术支持 API endpoints
包含：支持工单管理、技术方案管理、方案模板库、投标管理、售前统计
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.common.date_range import get_month_range
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.presale import (
    PresaleTenderRecord,
)
from app.models.sales import Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.presale import (
    TenderCreate,
    TenderResponse,
    TenderResultUpdate,
)

# 使用统一的编码生成工具
from app.utils.domain_codes import presale as presale_codes
from app.utils.db_helpers import get_or_404, save_obj

generate_ticket_no = presale_codes.generate_ticket_no
generate_solution_no = presale_codes.generate_solution_no
generate_tender_no = presale_codes.generate_tender_no

router = APIRouter(
    tags=["bids"]
)

# 共 5 个路由

# ==================== 投标管理 ====================

@router.get("/tenders", response_model=PaginatedResponse)
def read_tenders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（招标编号/项目名称）"),
    result: Optional[str] = Query(None, description="结果筛选"),
    customer_name: Optional[str] = Query(None, description="招标单位筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标记录列表
    """
    query = db.query(PresaleTenderRecord)

    query = apply_keyword_filter(query, PresaleTenderRecord, keyword, ["tender_no", "tender_name"])

    if result:
        query = query.filter(PresaleTenderRecord.result == result)

    # 应用关键词过滤（招标单位）
    query = apply_keyword_filter(query, PresaleTenderRecord, customer_name, ["customer_name"])

    total = query.count()
    tenders = apply_pagination(query.order_by(desc(PresaleTenderRecord.created_at)), pagination.offset, pagination.limit).all()

    items = []
    for tender in tenders:
        items.append(TenderResponse(
            id=tender.id,
            ticket_id=tender.ticket_id,
            opportunity_id=tender.opportunity_id,
            tender_no=tender.tender_no,
            tender_name=tender.tender_name,
            customer_name=tender.customer_name,
            publish_date=tender.publish_date,
            deadline=tender.deadline,
            bid_opening_date=tender.bid_opening_date,
            budget_amount=float(tender.budget_amount) if tender.budget_amount else None,
            our_bid_amount=float(tender.our_bid_amount) if tender.our_bid_amount else None,
            technical_score=float(tender.technical_score) if tender.technical_score else None,
            commercial_score=float(tender.commercial_score) if tender.commercial_score else None,
            total_score=float(tender.total_score) if tender.total_score else None,
            result=tender.result,
            result_reason=tender.result_reason,
            leader_id=tender.leader_id,
            created_at=tender.created_at,
            updated_at=tender.updated_at,
        ))

    return pagination.to_response(items, total)


@router.post("/tenders", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
def create_tender(
    *,
    db: Session = Depends(deps.get_db),
    tender_in: TenderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建投标记录
    """
    tender = PresaleTenderRecord(
        ticket_id=tender_in.ticket_id,
        opportunity_id=tender_in.opportunity_id,
        tender_no=tender_in.tender_no or generate_tender_no(db),
        tender_name=tender_in.tender_name,
        customer_name=tender_in.customer_name,
        publish_date=tender_in.publish_date,
        deadline=tender_in.deadline,
        bid_opening_date=tender_in.bid_opening_date,
        budget_amount=tender_in.budget_amount,
        qualification_requirements=tender_in.qualification_requirements,
        technical_requirements=tender_in.technical_requirements,
        our_bid_amount=tender_in.our_bid_amount,
        competitors=tender_in.competitors,
        result='PENDING',
        leader_id=tender_in.leader_id,
        team_members=tender_in.team_members
    )

    save_obj(db, tender)

    return TenderResponse(
        id=tender.id,
        ticket_id=tender.ticket_id,
        opportunity_id=tender.opportunity_id,
        tender_no=tender.tender_no,
        tender_name=tender.tender_name,
        customer_name=tender.customer_name,
        publish_date=tender.publish_date,
        deadline=tender.deadline,
        bid_opening_date=tender.bid_opening_date,
        budget_amount=float(tender.budget_amount) if tender.budget_amount else None,
        our_bid_amount=float(tender.our_bid_amount) if tender.our_bid_amount else None,
        technical_score=float(tender.technical_score) if tender.technical_score else None,
        commercial_score=float(tender.commercial_score) if tender.commercial_score else None,
        total_score=float(tender.total_score) if tender.total_score else None,
        result=tender.result,
        result_reason=tender.result_reason,
        leader_id=tender.leader_id,
        created_at=tender.created_at,
        updated_at=tender.updated_at,
    )


@router.get("/tenders/{tender_id}", response_model=TenderResponse)
def read_tender(
    *,
    db: Session = Depends(deps.get_db),
    tender_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标详情
    """
    tender = get_or_404(db, PresaleTenderRecord, tender_id, detail="投标记录不存在")

    return TenderResponse(
        id=tender.id,
        ticket_id=tender.ticket_id,
        opportunity_id=tender.opportunity_id,
        tender_no=tender.tender_no,
        tender_name=tender.tender_name,
        customer_name=tender.customer_name,
        publish_date=tender.publish_date,
        deadline=tender.deadline,
        bid_opening_date=tender.bid_opening_date,
        budget_amount=float(tender.budget_amount) if tender.budget_amount else None,
        our_bid_amount=float(tender.our_bid_amount) if tender.our_bid_amount else None,
        technical_score=float(tender.technical_score) if tender.technical_score else None,
        commercial_score=float(tender.commercial_score) if tender.commercial_score else None,
        total_score=float(tender.total_score) if tender.total_score else None,
        result=tender.result,
        result_reason=tender.result_reason,
        leader_id=tender.leader_id,
        created_at=tender.created_at,
        updated_at=tender.updated_at,
    )


@router.put("/tenders/{tender_id}/result", response_model=TenderResponse)
def update_tender_result(
    *,
    db: Session = Depends(deps.get_db),
    tender_id: int,
    result_request: TenderResultUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新投标结果
    """
    tender = get_or_404(db, PresaleTenderRecord, tender_id, detail="投标记录不存在")

    tender.result = result_request.result
    tender.result_reason = result_request.result_reason
    if result_request.technical_score:
        tender.technical_score = result_request.technical_score
    if result_request.commercial_score:
        tender.commercial_score = result_request.commercial_score
    if result_request.total_score:
        tender.total_score = result_request.total_score

    save_obj(db, tender)

    return TenderResponse(
        id=tender.id,
        ticket_id=tender.ticket_id,
        opportunity_id=tender.opportunity_id,
        tender_no=tender.tender_no,
        tender_name=tender.tender_name,
        customer_name=tender.customer_name,
        publish_date=tender.publish_date,
        deadline=tender.deadline,
        bid_opening_date=tender.bid_opening_date,
        budget_amount=float(tender.budget_amount) if tender.budget_amount else None,
        our_bid_amount=float(tender.our_bid_amount) if tender.our_bid_amount else None,
        technical_score=float(tender.technical_score) if tender.technical_score else None,
        commercial_score=float(tender.commercial_score) if tender.commercial_score else None,
        total_score=float(tender.total_score) if tender.total_score else None,
        result=tender.result,
        result_reason=tender.result_reason,
        leader_id=tender.leader_id,
        created_at=tender.created_at,
        updated_at=tender.updated_at,
    )


@router.get("/tenders/analysis", response_model=ResponseModel)
def get_tender_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标分析报表
    """

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        _, end_date = get_month_range(today)

    # 获取时间段内的投标记录
    tenders = db.query(PresaleTenderRecord).filter(
        PresaleTenderRecord.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleTenderRecord.created_at <= datetime.combine(end_date, datetime.max.time())
    ).all()

    # 统计结果
    total_tenders = len(tenders)
    won_count = len([t for t in tenders if t.result == 'WON'])
    lost_count = len([t for t in tenders if t.result == 'LOST'])
    pending_count = len([t for t in tenders if t.result == 'PENDING'])

    win_rate = (won_count / total_tenders * 100) if total_tenders > 0 else 0.0

    # 统计金额
    total_budget = sum(float(t.budget_amount or 0) for t in tenders)
    total_bid = sum(float(t.our_bid_amount or 0) for t in tenders)
    won_bid = sum(float(t.our_bid_amount or 0) for t in tenders if t.result == 'WON')

    # 按行业统计
    industry_stats = {}
    for tender in tenders:
        # 通过客户名称或商机获取行业（简化实现）
        industry = "其他"  # 默认值，实际应从关联表获取
        if tender.opportunity_id:
            opp = db.query(Opportunity).filter(Opportunity.id == tender.opportunity_id).first()
            if opp and opp.industry:
                industry = opp.industry

        if industry not in industry_stats:
            industry_stats[industry] = {"total": 0, "won": 0, "lost": 0, "pending": 0}

        industry_stats[industry]["total"] += 1
        if tender.result == 'WON':
            industry_stats[industry]["won"] += 1
        elif tender.result == 'LOST':
            industry_stats[industry]["lost"] += 1
        else:
            industry_stats[industry]["pending"] += 1

    # 按月份统计
    monthly_stats = {}
    for tender in tenders:
        month_key = tender.created_at.strftime("%Y-%m")
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {"total": 0, "won": 0, "lost": 0}

        monthly_stats[month_key]["total"] += 1
        if tender.result == 'WON':
            monthly_stats[month_key]["won"] += 1
        elif tender.result == 'LOST':
            monthly_stats[month_key]["lost"] += 1

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "summary": {
                "total_tenders": total_tenders,
                "won_count": won_count,
                "lost_count": lost_count,
                "pending_count": pending_count,
                "win_rate": round(win_rate, 2),
                "total_budget": round(total_budget, 2),
                "total_bid": round(total_bid, 2),
                "won_bid": round(won_bid, 2)
            },
            "by_industry": [
                {
                    "industry": industry,
                    "total": stats["total"],
                    "won": stats["won"],
                    "lost": stats["lost"],
                    "pending": stats["pending"],
                    "win_rate": round((stats["won"] / stats["total"] * 100) if stats["total"] > 0 else 0.0, 2)
                }
                for industry, stats in industry_stats.items()
            ],
            "by_month": [
                {
                    "month": month,
                    "total": stats["total"],
                    "won": stats["won"],
                    "lost": stats["lost"],
                    "win_rate": round((stats["won"] / stats["total"] * 100) if stats["total"] > 0 else 0.0, 2)
                }
                for month, stats in sorted(monthly_stats.items())
            ]
        }
    )



