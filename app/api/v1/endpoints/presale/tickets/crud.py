# -*- coding: utf-8 -*-
"""
售前工单管理 - CRUD操作
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.sales_permissions import can_manage_sales_opportunity
from app.common.query_filters import apply_keyword_filter
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.presale import PresaleSupportTicket
from app.models.sales import Opportunity
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.presale import TicketCreate, TicketResponse

from .utils import build_ticket_response, generate_ticket_no

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def read_tickets(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
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

    query = apply_keyword_filter(query, PresaleSupportTicket, keyword, ["ticket_no", "title"])

    if status:
        if "," in status:
            status_values = [item.strip() for item in status.split(",") if item.strip()]
            if status_values:
                query = query.filter(PresaleSupportTicket.status.in_(status_values))
        else:
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
    tickets = apply_pagination(query.order_by(desc(PresaleSupportTicket.created_at)), pagination.offset, pagination.limit).all()

    items = [build_ticket_response(ticket) for ticket in tickets]

    return pagination.to_response(items, total)


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    *,
    db: Session = Depends(deps.get_db),
    ticket_in: TicketCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建支持申请
    """
    from datetime import datetime

    if ticket_in.ticket_type == 'SOLUTION_REVIEW':
        if not ticket_in.opportunity_id:
            raise HTTPException(status_code=400, detail="方案评审必须关联商机")
        opportunity = db.query(Opportunity).filter(Opportunity.id == ticket_in.opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="商机不存在")
        gate_status = (opportunity.gate_status or "").upper()
        if gate_status not in {"PASS", "PASSED"}:
            raise HTTPException(status_code=400, detail="商机阶段门未通过，无法申请评审")
        if not can_manage_sales_opportunity(db, current_user, opportunity):
            raise HTTPException(status_code=403, detail="无权限为该商机申请评审")

    ticket_status = 'REVIEW' if ticket_in.ticket_type == 'SOLUTION_REVIEW' else 'PENDING'
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
        status=ticket_status,
        created_by=current_user.id
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return build_ticket_response(ticket)


@router.get("/{ticket_id}", response_model=TicketResponse)
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

    return build_ticket_response(ticket)
