# -*- coding: utf-8 -*-
"""
售前工单管理 - 看板视图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.presale import PresaleSupportTicket
from app.models.user import User
from app.schemas.presale import TicketBoardResponse

from .utils import build_ticket_response

router = APIRouter()


@router.get("/board", response_model=TicketBoardResponse)
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
        ticket_resp = build_ticket_response(ticket)

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
