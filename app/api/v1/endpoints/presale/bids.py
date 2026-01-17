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
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.presale import (
    PresaleSolution,
    PresaleSolutionCost,
    PresaleSolutionTemplate,
    PresaleSupportTicket,
    PresaleTenderRecord,
    PresaleTicketDeliverable,
    PresaleTicketProgress,
    PresaleWorkload,
)
from app.models.project import Project
from app.models.sales import Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.presale import (
    DeliverableCreate,
    DeliverableResponse,
    SolutionCostResponse,
    SolutionCreate,
    SolutionResponse,
    SolutionReviewRequest,
    SolutionUpdate,
    TemplateCreate,
    TemplateResponse,
    TenderCreate,
    TenderResponse,
    TenderResultUpdate,
    TicketAcceptRequest,
    TicketBoardResponse,
    TicketCreate,
    TicketProgressUpdate,
    TicketRatingRequest,
    TicketResponse,
    TicketUpdate,
)

router = APIRouter()


def generate_ticket_no(db: Session) -> str:
    """生成工单编号：TICKET-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_ticket = (
        db.query(PresaleSupportTicket)
        .filter(PresaleSupportTicket.ticket_no.like(f"TICKET-{today}-%"))
        .order_by(desc(PresaleSupportTicket.ticket_no))
        .first()
    )
    if max_ticket:
        seq = int(max_ticket.ticket_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"TICKET-{today}-{seq:03d}"


def generate_solution_no(db: Session) -> str:
    """生成方案编号：SOL-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_solution = (
        db.query(PresaleSolution)
        .filter(PresaleSolution.solution_no.like(f"SOL-{today}-%"))
        .order_by(desc(PresaleSolution.solution_no))
        .first()
    )
    if max_solution:
        seq = int(max_solution.solution_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"SOL-{today}-{seq:03d}"


def generate_tender_no(db: Session) -> str:
    """生成投标编号：TENDER-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_tender = (
        db.query(PresaleTenderRecord)
        .filter(PresaleTenderRecord.tender_no.like(f"TENDER-{today}-%"))
        .order_by(desc(PresaleTenderRecord.tender_no))
        .first()
    )
    if max_tender:
        seq = int(max_tender.tender_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"TENDER-{today}-{seq:03d}"



from fastapi import APIRouter

router = APIRouter(
    prefix="/presale/bids",
    tags=["bids"]
)

# 共 5 个路由

# ==================== 投标管理 ====================

@router.get("/presale/tenders", response_model=PaginatedResponse)
def read_tenders(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（招标编号/项目名称）"),
    result: Optional[str] = Query(None, description="结果筛选"),
    customer_name: Optional[str] = Query(None, description="招标单位筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标记录列表
    """
    query = db.query(PresaleTenderRecord)

    if keyword:
        query = query.filter(
            or_(
                PresaleTenderRecord.tender_no.like(f"%{keyword}%"),
                PresaleTenderRecord.tender_name.like(f"%{keyword}%"),
            )
        )

    if result:
        query = query.filter(PresaleTenderRecord.result == result)

    if customer_name:
        query = query.filter(PresaleTenderRecord.customer_name.like(f"%{customer_name}%"))

    total = query.count()
    offset = (page - 1) * page_size
    tenders = query.order_by(desc(PresaleTenderRecord.created_at)).offset(offset).limit(page_size).all()

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

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/presale/tenders", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
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

    db.add(tender)
    db.commit()
    db.refresh(tender)

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


@router.get("/presale/tenders/{tender_id}", response_model=TenderResponse)
def read_tender(
    *,
    db: Session = Depends(deps.get_db),
    tender_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标详情
    """
    tender = db.query(PresaleTenderRecord).filter(PresaleTenderRecord.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="投标记录不存在")

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


@router.put("/presale/tenders/{tender_id}/result", response_model=TenderResponse)
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
    tender = db.query(PresaleTenderRecord).filter(PresaleTenderRecord.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="投标记录不存在")

    tender.result = result_request.result
    tender.result_reason = result_request.result_reason
    if result_request.technical_score:
        tender.technical_score = result_request.technical_score
    if result_request.commercial_score:
        tender.commercial_score = result_request.commercial_score
    if result_request.total_score:
        tender.total_score = result_request.total_score

    db.add(tender)
    db.commit()
    db.refresh(tender)

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


@router.get("/presale/tenders/analysis", response_model=ResponseModel)
def get_tender_analysis(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    投标分析报表
    """
    from datetime import timedelta

    # 默认使用当前月
    today = date.today()
    if not start_date:
        start_date = date(today.year, today.month, 1)
    if not end_date:
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

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



