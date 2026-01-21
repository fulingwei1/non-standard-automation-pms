# -*- coding: utf-8 -*-
"""
服务工单管理 - 统计
"""
from typing import Any

from fastapi import Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import ServiceTicket
from app.models.user import User

from fastapi import APIRouter

router = APIRouter()


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_service_ticket_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取服务工单统计
    """
    total = db.query(ServiceTicket).count()
    pending = db.query(ServiceTicket).filter(ServiceTicket.status == "PENDING").count()
    in_progress = db.query(ServiceTicket).filter(ServiceTicket.status == "IN_PROGRESS").count()
    resolved = db.query(ServiceTicket).filter(ServiceTicket.status == "RESOLVED").count()
    closed = db.query(ServiceTicket).filter(ServiceTicket.status == "CLOSED").count()
    urgent = db.query(ServiceTicket).filter(ServiceTicket.urgency == "URGENT").count()

    return {
        "total": total,
        "pending": pending,
        "in_progress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "urgent": urgent,
    }
