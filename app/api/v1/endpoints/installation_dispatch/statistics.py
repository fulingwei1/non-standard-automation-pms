# -*- coding: utf-8 -*-
"""
安装调试派工统计端点
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.user import User
from app.schemas.installation_dispatch import InstallationDispatchStatistics

router = APIRouter()


@router.get("/statistics", response_model=InstallationDispatchStatistics, status_code=status.HTTP_200_OK)
def get_installation_dispatch_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    获取安装调试派工统计
    """
    total = db.query(InstallationDispatchOrder).count()
    pending = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "PENDING").count()
    assigned = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "ASSIGNED").count()
    in_progress = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "IN_PROGRESS").count()
    completed = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "COMPLETED").count()
    cancelled = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.status == "CANCELLED").count()
    urgent = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.priority == "URGENT").count()

    return InstallationDispatchStatistics(
        total=total,
        pending=pending,
        assigned=assigned,
        in_progress=in_progress,
        completed=completed,
        cancelled=cancelled,
        urgent=urgent,
    )
