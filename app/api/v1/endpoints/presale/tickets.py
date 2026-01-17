# -*- coding: utf-8 -*-
"""
支持工单管理 - 自动生成
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
    prefix="/presale/tickets",
    tags=["tickets"]
)

# 共 9 个路由

# ==================== 支持工单管理 ====================

@router.get("/presale/tickets", response_model=PaginatedResponse)
def read_tickets(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（工单编号/标题）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    ticket_type: Optional[str] = Query(None, description="工单类型筛选"),
    applicant_id: Optional[int] = Query(None, description="申请人ID筛选"),
    assignee_id: Optional[int] = Query(None, description="处理人ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单列表
    """
    query = db.query(PresaleSupportTicket)

    if keyword:
        query = query.filter(
            or_(
                PresaleSupportTicket.ticket_no.like(f"%{keyword}%"),
                PresaleSupportTicket.title.like(f"%{keyword}%"),
            )
        )

    if status:
        query = query.filter(PresaleSupportTicket.status == status)

    if ticket_type:
        query = query.filter(PresaleSupportTicket.ticket_type == ticket_type)

    if applicant_id:
        query = query.filter(PresaleSupportTicket.applicant_id == applicant_id)

    if assignee_id:
        query = query.filter(PresaleSupportTicket.assignee_id == assignee_id)

    if customer_id:
        query = query.filter(PresaleSupportTicket.customer_id == customer_id)

    total = query.count()
    offset = (page - 1) * page_size
    tickets = query.order_by(desc(PresaleSupportTicket.created_at)).offset(offset).limit(page_size).all()

    items = []
    for ticket in tickets:
        items.append(TicketResponse(
            id=ticket.id,
            ticket_no=ticket.ticket_no,
            title=ticket.title,
            ticket_type=ticket.ticket_type,
            urgency=ticket.urgency,
            description=ticket.description,
            customer_id=ticket.customer_id,
            customer_name=ticket.customer_name,
            opportunity_id=ticket.opportunity_id,
            project_id=ticket.project_id,
            applicant_id=ticket.applicant_id,
            applicant_name=ticket.applicant_name,
            applicant_dept=ticket.applicant_dept,
            apply_time=ticket.apply_time,
            assignee_id=ticket.assignee_id,
            assignee_name=ticket.assignee_name,
            accept_time=ticket.accept_time,
            expected_date=ticket.expected_date,
            deadline=ticket.deadline,
            status=ticket.status,
            complete_time=ticket.complete_time,
            actual_hours=float(ticket.actual_hours) if ticket.actual_hours else None,
            satisfaction_score=ticket.satisfaction_score,
            feedback=ticket.feedback,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/presale/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: TicketCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建支持申请
    """
    ticket = PresaleSupportTicket(
        ticket_no=generate_ticket_no(db),
        title=ticket_in.title,
        ticket_type=ticket_in.ticket_type,
        urgency=ticket_in.urgency,
        description=ticket_in.description,
        customer_id=ticket_in.customer_id,
        customer_name=ticket_in.customer_name,
        opportunity_id=ticket_in.opportunity_id,
        project_id=ticket_in.project_id,
        applicant_id=current_user.id,
        applicant_name=current_user.real_name or current_user.username,
        applicant_dept=current_user.department,
        apply_time=datetime.now(),
        expected_date=ticket_in.expected_date,
        deadline=ticket_in.deadline,
        status='PENDING',
        created_by=current_user.id
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketResponse(
        id=ticket.id,
        ticket_no=ticket.ticket_no,
        title=ticket.title,
        ticket_type=ticket.ticket_type,
        urgency=ticket.urgency,
        description=ticket.description,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer_name,
        opportunity_id=ticket.opportunity_id,
        project_id=ticket.project_id,
        applicant_id=ticket.applicant_id,
        applicant_name=ticket.applicant_name,
        applicant_dept=ticket.applicant_dept,
        apply_time=ticket.apply_time,
        assignee_id=ticket.assignee_id,
        assignee_name=ticket.assignee_name,
        accept_time=ticket.accept_time,
        expected_date=ticket.expected_date,
        deadline=ticket.deadline,
        status=ticket.status,
        complete_time=ticket.complete_time,
        actual_hours=float(ticket.actual_hours) if ticket.actual_hours else None,
        satisfaction_score=ticket.satisfaction_score,
        feedback=ticket.feedback,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


@router.get("/presale/tickets/{ticket_id}", response_model=TicketResponse)
def read_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单详情
    """
    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    return TicketResponse(
        id=ticket.id,
        ticket_no=ticket.ticket_no,
        title=ticket.title,
        ticket_type=ticket.ticket_type,
        urgency=ticket.urgency,
        description=ticket.description,
        customer_id=ticket.customer_id,
        customer_name=ticket.customer_name,
        opportunity_id=ticket.opportunity_id,
        project_id=ticket.project_id,
        applicant_id=ticket.applicant_id,
        applicant_name=ticket.applicant_name,
        applicant_dept=ticket.applicant_dept,
        apply_time=ticket.apply_time,
        assignee_id=ticket.assignee_id,
        assignee_name=ticket.assignee_name,
        accept_time=ticket.accept_time,
        expected_date=ticket.expected_date,
        deadline=ticket.deadline,
        status=ticket.status,
        complete_time=ticket.complete_time,
        actual_hours=float(ticket.actual_hours) if ticket.actual_hours else None,
        satisfaction_score=ticket.satisfaction_score,
        feedback=ticket.feedback,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


@router.put("/presale/tickets/{ticket_id}/accept", response_model=TicketResponse)
def accept_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    accept_request: TicketAcceptRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    接单确认
    """
    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    if ticket.status != 'PENDING':
        raise HTTPException(status_code=400, detail="只有待处理状态的工单才能接单")

    assignee_id = accept_request.assignee_id or current_user.id
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="处理人不存在")

    ticket.assignee_id = assignee_id
    ticket.assignee_name = assignee.real_name or assignee.username
    ticket.accept_time = datetime.now()
    ticket.status = 'ACCEPTED'

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.put("/presale/tickets/{ticket_id}/progress", response_model=TicketResponse)
def update_ticket_progress(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    progress_request: TicketProgressUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新进度
    """
    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    if ticket.status not in ['ACCEPTED', 'IN_PROGRESS']:
        raise HTTPException(status_code=400, detail="只有已接单或进行中的工单才能更新进度")

    ticket.status = 'IN_PROGRESS'

    # 记录进度
    progress = PresaleTicketProgress(
        ticket_id=ticket_id,
        progress_note=progress_request.progress_note,
        progress_percent=progress_request.progress_percent,
        updated_by=current_user.id,
        updated_at=datetime.now()
    )
    db.add(progress)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.post("/presale/tickets/{ticket_id}/deliverables", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED)
def create_deliverable(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    deliverable_in: DeliverableCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交交付物
    """
    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    deliverable = PresaleTicketDeliverable(
        ticket_id=ticket_id,
        deliverable_name=deliverable_in.deliverable_name,
        deliverable_type=deliverable_in.deliverable_type,
        file_path=deliverable_in.file_path,
        file_url=deliverable_in.file_url,
        description=deliverable_in.description,
        created_by=current_user.id
    )

    db.add(deliverable)
    db.commit()
    db.refresh(deliverable)

    return DeliverableResponse(
        id=deliverable.id,
        ticket_id=deliverable.ticket_id,
        deliverable_name=deliverable.deliverable_name,
        deliverable_type=deliverable.deliverable_type,
        file_path=deliverable.file_path,
        file_url=deliverable.file_url,
        description=deliverable.description,
        created_at=deliverable.created_at,
        updated_at=deliverable.updated_at,
    )


@router.put("/presale/tickets/{ticket_id}/complete", response_model=TicketResponse)
def complete_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    actual_hours: Optional[float] = Query(None, description="实际工时"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单
    """
    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    ticket.status = 'COMPLETED'
    ticket.complete_time = datetime.now()
    if actual_hours:
        ticket.actual_hours = Decimal(str(actual_hours))

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.put("/presale/tickets/{ticket_id}/rating", response_model=TicketResponse)
def rate_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_id: int,
    rating_request: TicketRatingRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    满意度评价
    """
    ticket = db.query(PresaleSupportTicket).filter(PresaleSupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    if ticket.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有申请人才能评价")

    ticket.satisfaction_score = rating_request.satisfaction_score
    ticket.feedback = rating_request.feedback

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.get("/presale/tickets/board", response_model=TicketBoardResponse)
def get_ticket_board(
    db: Session = Depends(deps.get_db),
    assignee_id: Optional[int] = Query(None, description="处理人ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工单看板
    """
    query = db.query(PresaleSupportTicket)

    if assignee_id:
        query = query.filter(PresaleSupportTicket.assignee_id == assignee_id)

    tickets = query.order_by(PresaleSupportTicket.created_at).all()

    pending = []
    accepted = []
    in_progress = []
    completed = []

    for ticket in tickets:
        ticket_resp = TicketResponse(
            id=ticket.id,
            ticket_no=ticket.ticket_no,
            title=ticket.title,
            ticket_type=ticket.ticket_type,
            urgency=ticket.urgency,
            description=ticket.description,
            customer_id=ticket.customer_id,
            customer_name=ticket.customer_name,
            opportunity_id=ticket.opportunity_id,
            project_id=ticket.project_id,
            applicant_id=ticket.applicant_id,
            applicant_name=ticket.applicant_name,
            applicant_dept=ticket.applicant_dept,
            apply_time=ticket.apply_time,
            assignee_id=ticket.assignee_id,
            assignee_name=ticket.assignee_name,
            accept_time=ticket.accept_time,
            expected_date=ticket.expected_date,
            deadline=ticket.deadline,
            status=ticket.status,
            complete_time=ticket.complete_time,
            actual_hours=float(ticket.actual_hours) if ticket.actual_hours else None,
            satisfaction_score=ticket.satisfaction_score,
            feedback=ticket.feedback,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

        if ticket.status == 'PENDING':
            pending.append(ticket_resp)
        elif ticket.status == 'ACCEPTED':
            accepted.append(ticket_resp)
        elif ticket.status == 'IN_PROGRESS':
            in_progress.append(ticket_resp)
        elif ticket.status == 'COMPLETED':
            completed.append(ticket_resp)

    return TicketBoardResponse(
        pending=pending,
        accepted=accepted,
        in_progress=in_progress,
        completed=completed
    )



