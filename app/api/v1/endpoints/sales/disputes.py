# -*- coding: utf-8 -*-
"""
回款争议管理 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import ReceivableDispute
from app.schemas.sales import (
    ReceivableDisputeCreate, ReceivableDisputeResponse
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/disputes", response_model=PaginatedResponse[ReceivableDisputeResponse])
def read_disputes(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取回款争议列表
    """
    query = db.query(ReceivableDispute)

    if status:
        query = query.filter(ReceivableDispute.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    disputes = query.order_by(desc(ReceivableDispute.created_at)).offset(offset).limit(page_size).all()

    dispute_responses = []
    for dispute in disputes:
        dispute_dict = {
            **{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns},
            "responsible_name": dispute.responsible.real_name if dispute.responsible else None,
        }
        dispute_responses.append(ReceivableDisputeResponse(**dispute_dict))

    return PaginatedResponse(
        items=dispute_responses,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/disputes", response_model=ReceivableDisputeResponse, status_code=201)
def create_dispute(
    *,
    db: Session = Depends(deps.get_db),
    dispute_in: ReceivableDisputeCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建回款争议
    """
    dispute = ReceivableDispute(**dispute_in.model_dump())
    db.add(dispute)
    db.commit()
    db.refresh(dispute)

    dispute_dict = {
        **{c.name: getattr(dispute, c.name) for c in dispute.__table__.columns},
        "responsible_name": dispute.responsible.real_name if dispute.responsible else None,
    }
    return ReceivableDisputeResponse(**dispute_dict)
