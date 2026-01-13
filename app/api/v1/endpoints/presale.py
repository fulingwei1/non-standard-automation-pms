# -*- coding: utf-8 -*-
"""
售前技术支持 API endpoints
包含：支持工单管理、技术方案管理、方案模板库、投标管理、售前统计
"""
from typing import Any, List, Optional, Dict
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.project import Project
from app.models.sales import Opportunity
from app.models.presale import (
    PresaleSupportTicket, PresaleTicketDeliverable, PresaleTicketProgress,
    PresaleSolution, PresaleSolutionCost, PresaleSolutionTemplate,
    PresaleTenderRecord, PresaleWorkload
)
from app.schemas.presale import (
    TicketCreate, TicketUpdate, TicketResponse, TicketAcceptRequest,
    TicketProgressUpdate, DeliverableCreate, DeliverableResponse,
    TicketRatingRequest, TicketBoardResponse,
    SolutionCreate, SolutionUpdate, SolutionResponse, SolutionReviewRequest,
    SolutionCostResponse,
    TemplateCreate, TemplateResponse,
    TenderCreate, TenderResultUpdate, TenderResponse
)
from app.models.presale import PresaleSolutionTemplate
from app.schemas.common import ResponseModel, PaginatedResponse

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


# ==================== 技术方案管理 ====================

@router.get("/presale/solutions", response_model=PaginatedResponse)
def read_solutions(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（方案编号/名称）"),
    status: Optional[str] = Query(None, description="状态筛选"),
    solution_type: Optional[str] = Query(None, description="方案类型筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    ticket_id: Optional[int] = Query(None, description="工单ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案列表
    """
    query = db.query(PresaleSolution)
    
    if keyword:
        query = query.filter(
            or_(
                PresaleSolution.solution_no.like(f"%{keyword}%"),
                PresaleSolution.name.like(f"%{keyword}%"),
            )
        )
    
    if status:
        query = query.filter(PresaleSolution.status == status)
    
    if solution_type:
        query = query.filter(PresaleSolution.solution_type == solution_type)
    
    if industry:
        query = query.filter(PresaleSolution.industry == industry)
    
    if ticket_id:
        query = query.filter(PresaleSolution.ticket_id == ticket_id)
    
    total = query.count()
    offset = (page - 1) * page_size
    solutions = query.order_by(desc(PresaleSolution.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for solution in solutions:
        items.append(SolutionResponse(
            id=solution.id,
            solution_no=solution.solution_no,
            name=solution.name,
            solution_type=solution.solution_type,
            industry=solution.industry,
            test_type=solution.test_type,
            ticket_id=solution.ticket_id,
            customer_id=solution.customer_id,
            opportunity_id=solution.opportunity_id,
            requirement_summary=solution.requirement_summary,
            solution_overview=solution.solution_overview,
            technical_spec=solution.technical_spec,
            estimated_cost=float(solution.estimated_cost) if solution.estimated_cost else None,
            suggested_price=float(solution.suggested_price) if solution.suggested_price else None,
            cost_breakdown=solution.cost_breakdown,
            estimated_hours=solution.estimated_hours,
            estimated_duration=solution.estimated_duration,
            status=solution.status,
            version=solution.version,
            parent_id=solution.parent_id,
            reviewer_id=solution.reviewer_id,
            review_time=solution.review_time,
            review_status=solution.review_status,
            review_comment=solution.review_comment,
            created_at=solution.created_at,
            updated_at=solution.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/presale/solutions", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
def create_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_in: SolutionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建方案
    """
    solution = PresaleSolution(
        solution_no=generate_solution_no(db),
        name=solution_in.name,
        solution_type=solution_in.solution_type,
        industry=solution_in.industry,
        test_type=solution_in.test_type,
        ticket_id=solution_in.ticket_id,
        customer_id=solution_in.customer_id,
        opportunity_id=solution_in.opportunity_id,
        requirement_summary=solution_in.requirement_summary,
        solution_overview=solution_in.solution_overview,
        technical_spec=solution_in.technical_spec,
        estimated_cost=solution_in.estimated_cost,
        suggested_price=solution_in.suggested_price,
        estimated_hours=solution_in.estimated_hours,
        estimated_duration=solution_in.estimated_duration,
        status='DRAFT',
        version='V1.0',
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username
    )
    
    db.add(solution)
    db.commit()
    db.refresh(solution)
    
    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        customer_id=solution.customer_id,
        opportunity_id=solution.opportunity_id,
        requirement_summary=solution.requirement_summary,
        solution_overview=solution.solution_overview,
        technical_spec=solution.technical_spec,
        estimated_cost=float(solution.estimated_cost) if solution.estimated_cost else None,
        suggested_price=float(solution.suggested_price) if solution.suggested_price else None,
        cost_breakdown=solution.cost_breakdown,
        estimated_hours=solution.estimated_hours,
        estimated_duration=solution.estimated_duration,
        status=solution.status,
        version=solution.version,
        parent_id=solution.parent_id,
        reviewer_id=solution.reviewer_id,
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )


@router.get("/presale/solutions/{solution_id}", response_model=SolutionResponse)
def read_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案详情
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        customer_id=solution.customer_id,
        opportunity_id=solution.opportunity_id,
        requirement_summary=solution.requirement_summary,
        solution_overview=solution.solution_overview,
        technical_spec=solution.technical_spec,
        estimated_cost=float(solution.estimated_cost) if solution.estimated_cost else None,
        suggested_price=float(solution.suggested_price) if solution.suggested_price else None,
        cost_breakdown=solution.cost_breakdown,
        estimated_hours=solution.estimated_hours,
        estimated_duration=solution.estimated_duration,
        status=solution.status,
        version=solution.version,
        parent_id=solution.parent_id,
        reviewer_id=solution.reviewer_id,
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )


@router.put("/presale/solutions/{solution_id}", response_model=SolutionResponse)
def update_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    solution_in: SolutionUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新方案
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    if solution.status not in ['DRAFT', 'REJECTED']:
        raise HTTPException(status_code=400, detail="只有草稿或已驳回状态的方案才能修改")
    
    update_data = solution_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(solution, field, value)
    
    db.add(solution)
    db.commit()
    db.refresh(solution)
    
    return read_solution(db=db, solution_id=solution_id, current_user=current_user)


@router.get("/presale/solutions/{solution_id}/cost", response_model=SolutionCostResponse)
def get_solution_cost(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本估算
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    # 获取成本明细
    cost_items = db.query(PresaleSolutionCost).filter(
        PresaleSolutionCost.solution_id == solution_id
    ).order_by(PresaleSolutionCost.sort_order).all()
    
    breakdown = []
    total_cost = 0.0
    
    for item in cost_items:
        amount = float(item.amount) if item.amount else 0.0
        total_cost += amount
        breakdown.append({
            'id': item.id,
            'category': item.category,
            'item_name': item.item_name,
            'specification': item.specification,
            'unit': item.unit,
            'quantity': float(item.quantity) if item.quantity else 0.0,
            'unit_price': float(item.unit_price) if item.unit_price else 0.0,
            'amount': amount,
            'remark': item.remark
        })
    
    # 如果没有明细，使用方案中的预估成本
    if total_cost == 0 and solution.estimated_cost:
        total_cost = float(solution.estimated_cost)
    
    return SolutionCostResponse(
        solution_id=solution_id,
        total_cost=total_cost,
        breakdown=breakdown
    )


@router.put("/presale/solutions/{solution_id}/review", response_model=SolutionResponse)
def review_solution(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    review_request: SolutionReviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案审核
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    solution.review_status = review_request.review_status
    solution.review_comment = review_request.review_comment
    solution.reviewer_id = current_user.id
    solution.review_time = datetime.now()
    
    if review_request.review_status == 'APPROVED':
        solution.status = 'APPROVED'
    elif review_request.review_status == 'REJECTED':
        solution.status = 'REJECTED'
    
    db.add(solution)
    db.commit()
    db.refresh(solution)
    
    return read_solution(db=db, solution_id=solution_id, current_user=current_user)



@router.get("/presale/solutions/{solution_id}/versions", response_model=List[SolutionResponse])
def get_solution_versions(
    *,
    db: Session = Depends(deps.get_db),
    solution_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案版本历史
    """
    solution = db.query(PresaleSolution).filter(PresaleSolution.id == solution_id).first()
    if not solution:
        raise HTTPException(status_code=404, detail="方案不存在")
    
    # 获取所有版本（包括当前版本和子版本）
    versions = []
    
    # 向上查找父版本
    current = solution
    while current.parent_id:
        parent = db.query(PresaleSolution).filter(PresaleSolution.id == current.parent_id).first()
        if parent:
            versions.insert(0, parent)
            current = parent
        else:
            break
    
    # 添加当前版本
    versions.append(solution)
    
    # 向下查找子版本
    child_versions = db.query(PresaleSolution).filter(
        PresaleSolution.parent_id == solution_id
    ).order_by(PresaleSolution.created_at).all()
    versions.extend(child_versions)
    
    result = []
    for sol in versions:
        result.append(SolutionResponse(
            id=sol.id,
            solution_no=sol.solution_no,
            name=sol.name,
            solution_type=sol.solution_type,
            industry=sol.industry,
            test_type=sol.test_type,
            ticket_id=sol.ticket_id,
            customer_id=sol.customer_id,
            opportunity_id=sol.opportunity_id,
            requirement_summary=sol.requirement_summary,
            solution_overview=sol.solution_overview,
            technical_spec=sol.technical_spec,
            estimated_cost=float(sol.estimated_cost) if sol.estimated_cost else None,
            suggested_price=float(sol.suggested_price) if sol.suggested_price else None,
            cost_breakdown=sol.cost_breakdown,
            estimated_hours=sol.estimated_hours,
            estimated_duration=sol.estimated_duration,
            status=sol.status,
            version=sol.version,
            parent_id=sol.parent_id,
            reviewer_id=sol.reviewer_id,
            review_time=sol.review_time,
            review_status=sol.review_status,
            review_comment=sol.review_comment,
            created_at=sol.created_at,
            updated_at=sol.updated_at,
        ))
    
    return result


# ==================== 方案模板库 ====================

@router.get("/presale/templates", response_model=PaginatedResponse)
def read_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（模板名称）"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    test_type: Optional[str] = Query(None, description="测试类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    模板列表
    """
    query = db.query(PresaleSolutionTemplate)
    
    if keyword:
        query = query.filter(PresaleSolutionTemplate.name.like(f"%{keyword}%"))
    
    if industry:
        query = query.filter(PresaleSolutionTemplate.industry == industry)
    
    if test_type:
        query = query.filter(PresaleSolutionTemplate.test_type == test_type)
    
    if is_active is not None:
        query = query.filter(PresaleSolutionTemplate.is_active == is_active)
    
    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(desc(PresaleSolutionTemplate.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for template in templates:
        items.append(TemplateResponse(
            id=template.id,
            template_no=template.template_no,
            name=template.name,
            industry=template.industry,
            test_type=template.test_type,
            description=template.description,
            use_count=template.use_count,
            is_active=template.is_active,
            created_at=template.created_at,
            updated_at=template.updated_at,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/presale/templates", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: TemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建模板
    """
    # 生成模板编号
    today = datetime.now().strftime("%y%m%d")
    max_template = (
        db.query(PresaleSolutionTemplate)
        .filter(PresaleSolutionTemplate.template_no.like(f"TMP-{today}-%"))
        .order_by(desc(PresaleSolutionTemplate.template_no))
        .first()
    )
    if max_template:
        seq = int(max_template.template_no.split("-")[-1]) + 1
    else:
        seq = 1
    template_no = f"TMP-{today}-{seq:03d}"
    
    template = PresaleSolutionTemplate(
        template_no=template_no,
        name=template_in.name,
        industry=template_in.industry,
        test_type=template_in.test_type,
        description=template_in.description,
        content_template=template_in.content_template,
        cost_template=template_in.cost_template,
        attachments=template_in.attachments,
        is_active=True,
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return TemplateResponse(
        id=template.id,
        template_no=template.template_no,
        name=template.name,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        use_count=template.use_count,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.get("/presale/templates/{template_id}", response_model=TemplateResponse)
def read_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    模板详情
    """
    template = db.query(PresaleSolutionTemplate).filter(PresaleSolutionTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return TemplateResponse(
        id=template.id,
        template_no=template.template_no,
        name=template.name,
        industry=template.industry,
        test_type=template.test_type,
        description=template.description,
        use_count=template.use_count,
        is_active=template.is_active,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/presale/templates/{template_id}/apply", response_model=SolutionResponse, status_code=status.HTTP_201_CREATED)
def apply_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    ticket_id: Optional[int] = Query(None, description="关联工单ID"),
    customer_id: Optional[int] = Query(None, description="客户ID"),
    opportunity_id: Optional[int] = Query(None, description="商机ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    从模板创建方案
    """
    template = db.query(PresaleSolutionTemplate).filter(PresaleSolutionTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已禁用")
    
    # 创建方案
    solution = PresaleSolution(
        solution_no=generate_solution_no(db),
        name=f"{template.name}（基于模板）",
        solution_type='STANDARD',
        industry=template.industry,
        test_type=template.test_type,
        ticket_id=ticket_id,
        customer_id=customer_id,
        opportunity_id=opportunity_id,
        requirement_summary=template.description,
        solution_overview=template.content_template,
        status='DRAFT',
        version='V1.0',
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username
    )
    
    db.add(solution)
    db.flush()
    
    # 如果模板有成本模板，创建成本明细
    if template.cost_template:
        # 解析cost_template JSON - 支持列表格式或包含items键的字典格式
        cost_items = template.cost_template
        if isinstance(cost_items, dict):
            cost_items = cost_items.get('items', [])

        if isinstance(cost_items, list):
            for idx, item in enumerate(cost_items):
                if not isinstance(item, dict):
                    continue

                # 计算金额（如果未提供）
                quantity = Decimal(str(item.get('quantity', 0) or 0))
                unit_price = Decimal(str(item.get('unit_price', 0) or 0))
                amount = item.get('amount')
                if amount is None:
                    amount = quantity * unit_price
                else:
                    amount = Decimal(str(amount))

                cost_record = PresaleSolutionCost(
                    solution_id=solution.id,
                    category=item.get('category', '其他'),
                    item_name=item.get('item_name', '未命名项目'),
                    specification=item.get('specification'),
                    unit=item.get('unit'),
                    quantity=quantity if quantity else None,
                    unit_price=unit_price if unit_price else None,
                    amount=amount if amount else None,
                    remark=item.get('remark'),
                    sort_order=item.get('sort_order', idx)
                )
                db.add(cost_record)
    
    # 更新模板使用次数
    template.use_count = (template.use_count or 0) + 1
    db.add(template)
    db.commit()
    db.refresh(solution)
    
    return SolutionResponse(
        id=solution.id,
        solution_no=solution.solution_no,
        name=solution.name,
        solution_type=solution.solution_type,
        industry=solution.industry,
        test_type=solution.test_type,
        ticket_id=solution.ticket_id,
        customer_id=solution.customer_id,
        opportunity_id=solution.opportunity_id,
        requirement_summary=solution.requirement_summary,
        solution_overview=solution.solution_overview,
        technical_spec=solution.technical_spec,
        estimated_cost=float(solution.estimated_cost) if solution.estimated_cost else None,
        suggested_price=float(solution.suggested_price) if solution.suggested_price else None,
        cost_breakdown=solution.cost_breakdown,
        estimated_hours=solution.estimated_hours,
        estimated_duration=solution.estimated_duration,
        status=solution.status,
        version=solution.version,
        parent_id=solution.parent_id,
        reviewer_id=solution.reviewer_id,
        review_time=solution.review_time,
        review_status=solution.review_status,
        review_comment=solution.review_comment,
        created_at=solution.created_at,
        updated_at=solution.updated_at,
    )


@router.get("/presale/templates/stats", response_model=ResponseModel)
def get_template_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    模板使用统计
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
    
    # 获取所有模板
    templates = db.query(PresaleSolutionTemplate).all()
    
    template_stats = []
    for template in templates:
        # 统计该模板在此时间段内创建方案的数量
        solutions_count = db.query(PresaleSolution).filter(
            PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
        ).filter(
            # 通过方案名称或内容匹配模板（简化实现，实际可以通过关联字段）
            PresaleSolution.solution_overview.like(f"%{template.name}%")
        ).count()
        
        # 计算复用率（使用次数 / 总方案数）
        total_solutions = db.query(PresaleSolution).filter(
            PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
        ).count()
        
        reuse_rate = (solutions_count / total_solutions * 100) if total_solutions > 0 else 0.0
        
        template_stats.append({
            "template_id": template.id,
            "template_no": template.template_no,
            "template_name": template.name,
            "industry": template.industry,
            "test_type": template.test_type,
            "total_use_count": template.use_count or 0,
            "period_use_count": solutions_count,
            "reuse_rate": round(reuse_rate, 2),
            "is_active": template.is_active
        })
    
    # 按使用次数排序
    template_stats.sort(key=lambda x: x["period_use_count"], reverse=True)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "templates": template_stats,
            "summary": {
                "total_templates": len(templates),
                "active_templates": len([t for t in templates if t.is_active]),
                "total_uses": sum(t["period_use_count"] for t in template_stats),
                "avg_reuse_rate": round(sum(t["reuse_rate"] for t in template_stats) / len(template_stats), 2) if template_stats else 0.0
            }
        }
    )


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


# ==================== 售前统计 ====================

@router.get("/presale/stats/workload", response_model=ResponseModel)
def get_workload_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="人员ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    工作量统计
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
    
    query = db.query(PresaleWorkload).filter(
        PresaleWorkload.stat_date >= start_date,
        PresaleWorkload.stat_date <= end_date
    )
    
    if user_id:
        query = query.filter(PresaleWorkload.user_id == user_id)
    
    workloads = query.all()
    
    # 汇总统计
    total_pending = sum(w.pending_tickets or 0 for w in workloads)
    total_processing = sum(w.processing_tickets or 0 for w in workloads)
    total_completed = sum(w.completed_tickets or 0 for w in workloads)
    total_planned_hours = sum(float(w.planned_hours or 0) for w in workloads)
    total_actual_hours = sum(float(w.actual_hours or 0) for w in workloads)
    total_solutions = sum(w.solutions_count or 0 for w in workloads)
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "summary": {
                "pending_tickets": total_pending,
                "processing_tickets": total_processing,
                "completed_tickets": total_completed,
                "total_tickets": total_pending + total_processing + total_completed,
                "planned_hours": round(total_planned_hours, 2),
                "actual_hours": round(total_actual_hours, 2),
                "solutions_count": total_solutions
            },
            "by_user": [
                {
                    "user_id": w.user_id,
                    "pending_tickets": w.pending_tickets or 0,
                    "processing_tickets": w.processing_tickets or 0,
                    "completed_tickets": w.completed_tickets or 0,
                    "planned_hours": float(w.planned_hours or 0),
                    "actual_hours": float(w.actual_hours or 0),
                    "solutions_count": w.solutions_count or 0
                }
                for w in workloads
            ]
        }
    )


@router.get("/presale/stats/response-time", response_model=ResponseModel)
def get_response_time_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    响应时效统计
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
    
    # 统计接单响应时间（从申请到接单的时间差）
    tickets = db.query(PresaleSupportTicket).filter(
        PresaleSupportTicket.apply_time >= datetime.combine(start_date, datetime.min.time()),
        PresaleSupportTicket.apply_time <= datetime.combine(end_date, datetime.max.time()),
        PresaleSupportTicket.accept_time.isnot(None)
    ).all()
    
    response_times = []
    for ticket in tickets:
        if ticket.accept_time and ticket.apply_time:
            delta = ticket.accept_time - ticket.apply_time
            response_times.append(delta.total_seconds() / 3600)  # 转换为小时
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
    
    # 统计完成时间（从接单到完成的时间差）
    completed_tickets = [t for t in tickets if t.complete_time]
    completion_times = []
    for ticket in completed_tickets:
        if ticket.complete_time and ticket.accept_time:
            delta = ticket.complete_time - ticket.accept_time
            completion_times.append(delta.total_seconds() / 3600)
    
    avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else 0.0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "response_time": {
                "total_tickets": len(tickets),
                "avg_response_hours": round(avg_response_time, 2),
                "min_response_hours": round(min(response_times), 2) if response_times else 0.0,
                "max_response_hours": round(max(response_times), 2) if response_times else 0.0
            },
            "completion_time": {
                "total_completed": len(completed_tickets),
                "avg_completion_hours": round(avg_completion_time, 2),
                "min_completion_hours": round(min(completion_times), 2) if completion_times else 0.0,
                "max_completion_hours": round(max(completion_times), 2) if completion_times else 0.0
            }
        }
    )


@router.get("/presale/stats/conversion", response_model=ResponseModel)
def get_conversion_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    方案转化率
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
    
    # 统计方案数量
    total_solutions = db.query(PresaleSolution).filter(
        PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
    ).count()
    
    # 统计关联商机的方案
    solutions_with_opp = db.query(PresaleSolution).filter(
        PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time()),
        PresaleSolution.opportunity_id.isnot(None)
    ).count()
    
    # 统计转化为项目的方案（通过商机 -> 合同 -> 项目）
    from app.models.sales import Contract
    solutions_with_opp_list = db.query(PresaleSolution).filter(
        PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
        PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time()),
        PresaleSolution.opportunity_id.isnot(None)
    ).all()
    
    converted_count = 0
    for solution in solutions_with_opp_list:
        if solution.opportunity_id:
            # 查找该商机是否有合同，且合同关联了项目
            contract = db.query(Contract).filter(
                Contract.opportunity_id == solution.opportunity_id,
                Contract.project_id.isnot(None)
            ).first()
            if contract:
                converted_count += 1
    
    conversion_rate = (converted_count / total_solutions * 100) if total_solutions > 0 else 0.0
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "total_solutions": total_solutions,
            "solutions_with_opportunity": solutions_with_opp,
            "converted_to_projects": converted_count,
            "conversion_rate": round(conversion_rate, 2)
        }
    )


@router.get("/presale/stats/performance", response_model=ResponseModel)
def get_performance_stats(
    db: Session = Depends(deps.get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    user_id: Optional[int] = Query(None, description="人员ID筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    人员绩效
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
    
    # 获取人员列表
    query_users = db.query(User).filter(User.is_active == True)
    if user_id:
        query_users = query_users.filter(User.id == user_id)
    users = query_users.all()
    
    performance_list = []
    for user in users:
        # 统计工单
        tickets = db.query(PresaleSupportTicket).filter(
            PresaleSupportTicket.assignee_id == user.id,
            PresaleSupportTicket.apply_time >= datetime.combine(start_date, datetime.min.time()),
            PresaleSupportTicket.apply_time <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        completed_tickets = [t for t in tickets if t.status == 'COMPLETED']
        total_hours = sum(float(t.actual_hours or 0) for t in completed_tickets)
        
        # 统计方案
        solutions = db.query(PresaleSolution).filter(
            PresaleSolution.author_id == user.id,
            PresaleSolution.created_at >= datetime.combine(start_date, datetime.min.time()),
            PresaleSolution.created_at <= datetime.combine(end_date, datetime.max.time())
        ).count()
        
        # 统计满意度
        rated_tickets = [t for t in completed_tickets if t.satisfaction_score]
        avg_satisfaction = sum(t.satisfaction_score for t in rated_tickets) / len(rated_tickets) if rated_tickets else 0.0
        
        performance_list.append({
            "user_id": user.id,
            "user_name": user.real_name or user.username,
            "total_tickets": len(tickets),
            "completed_tickets": len(completed_tickets),
            "completion_rate": (len(completed_tickets) / len(tickets) * 100) if tickets else 0.0,
            "total_hours": round(total_hours, 2),
            "solutions_count": solutions,
            "avg_satisfaction": round(avg_satisfaction, 2)
        })
    
    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {"start": str(start_date), "end": str(end_date)},
            "performance": performance_list
        }
    )
