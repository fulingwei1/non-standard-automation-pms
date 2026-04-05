# -*- coding: utf-8 -*-
"""
服务工单管理 - 统计
"""
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import ServiceTicket
from app.models.service.enums import ServiceTicketStatusEnum
from app.models.user import User

from ..access import filter_service_project_query

router = APIRouter()


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_service_ticket_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取服务工单统计
    """
    query = filter_service_project_query(db, db.query(ServiceTicket), current_user, ServiceTicket.project_id)

    pending_statuses = [
        ServiceTicketStatusEnum.PENDING.value,
        "DRAFT",
    ]
    in_progress_statuses = [
        ServiceTicketStatusEnum.IN_PROGRESS.value,
        "ACTIVE",
    ]
    resolved_statuses = [
        ServiceTicketStatusEnum.RESOLVED.value,
        "APPROVED",
    ]
    closed_statuses = [
        ServiceTicketStatusEnum.CLOSED.value,
        "COMPLETED",
    ]

    total = query.count()
    pending = query.filter(ServiceTicket.status.in_(pending_statuses)).count()
    in_progress = query.filter(ServiceTicket.status.in_(in_progress_statuses)).count()
    resolved = query.filter(ServiceTicket.status.in_(resolved_statuses)).count()
    closed = query.filter(ServiceTicket.status.in_(closed_statuses)).count()
    urgent = query.filter(ServiceTicket.urgency == "URGENT").count()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "urgent": urgent,
    }
