# -*- coding: utf-8 -*-
"""
回款争议管理 API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import ReceivableDispute
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import ReceivableDisputeCreate, ReceivableDisputeResponse
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.get("/disputes", response_model=PaginatedResponse[ReceivableDisputeResponse])
def read_disputes(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
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
    disputes = query.order_by(desc(ReceivableDispute.created_at)).offset(pagination.offset).limit(pagination.limit).all()

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
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
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
