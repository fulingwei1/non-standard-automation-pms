# -*- coding: utf-8 -*-
"""
售前工单管理 - 业务操作
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale import PresaleSupportTicket, PresaleTicketDeliverable, PresaleTicketProgress
from app.models.user import User
from app.schemas.presale import DeliverableCreate, DeliverableResponse, TicketAcceptRequest, TicketProgressUpdate, TicketRatingRequest, TicketResponse

from .crud import read_ticket
from app.utils.db_helpers import get_or_404, save_obj

router = APIRouter()


@router.put("/{ticket_id}/accept", response_model=TicketResponse)
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
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    if ticket.status != 'PENDING':
        raise HTTPException(status_code=400, detail="只有待处理状态的工单才能接单")

    assignee_id = accept_request.assignee_id or current_user.id
    assignee = get_or_404(db, User, assignee_id, detail="处理人不存在")

    ticket.assignee_id = assignee_id
    ticket.assignee_name = assignee.real_name or assignee.username
    ticket.accept_time = datetime.now()
    ticket.status = 'ACCEPTED'

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.put("/{ticket_id}/progress", response_model=TicketResponse)
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
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

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

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.post("/{ticket_id}/deliverables", response_model=DeliverableResponse, status_code=status.HTTP_201_CREATED)
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
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    deliverable = PresaleTicketDeliverable(
        ticket_id=ticket_id,
        deliverable_name=deliverable_in.deliverable_name,
        deliverable_type=deliverable_in.deliverable_type,
        file_path=deliverable_in.file_path,
        file_url=deliverable_in.file_url,
        description=deliverable_in.description,
        created_by=current_user.id
    )

    save_obj(db, deliverable)

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


@router.put("/{ticket_id}/complete", response_model=TicketResponse)
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
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    ticket.status = 'COMPLETED'
    ticket.complete_time = datetime.now()
    if actual_hours:
        ticket.actual_hours = Decimal(str(actual_hours))

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)


@router.put("/{ticket_id}/rating", response_model=TicketResponse)
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
    ticket = get_or_404(db, PresaleSupportTicket, ticket_id, detail="工单不存在")

    if ticket.applicant_id != current_user.id:
        raise HTTPException(status_code=403, detail="只有申请人才能评价")

    ticket.satisfaction_score = rating_request.satisfaction_score
    ticket.feedback = rating_request.feedback

    save_obj(db, ticket)

    return read_ticket(db=db, ticket_id=ticket_id, current_user=current_user)
