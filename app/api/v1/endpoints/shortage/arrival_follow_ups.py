# -*- coding: utf-8 -*-
"""
到货跟踪 - 跟进记录管理

包含跟进记录的列表和创建
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.shortage import ArrivalFollowUp, MaterialArrival
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.shortage import (
    ArrivalFollowUpCreate,
    ArrivalFollowUpResponse,
)

router = APIRouter()


@router.get("/shortage/arrivals/{arrival_id}/follow-ups", response_model=PaginatedResponse)
def read_arrival_follow_ups(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取到货跟踪的跟催记录列表
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    query = db.query(ArrivalFollowUp).filter(ArrivalFollowUp.arrival_id == arrival_id)

    total = query.count()
    offset = (page - 1) * page_size
    follow_ups = query.order_by(desc(ArrivalFollowUp.followed_at)).offset(offset).limit(page_size).all()

    items = []
    for follow_up in follow_ups:
        followed_by_user = db.query(User).filter(User.id == follow_up.followed_by).first()
        items.append(ArrivalFollowUpResponse(
            id=follow_up.id,
            arrival_id=follow_up.arrival_id,
            follow_up_type=follow_up.follow_up_type,
            follow_up_note=follow_up.follow_up_note,
            followed_by=follow_up.followed_by,
            followed_by_name=followed_by_user.real_name or followed_by_user.username if followed_by_user else None,
            followed_at=follow_up.followed_at,
            supplier_response=follow_up.supplier_response,
            next_follow_up_date=follow_up.next_follow_up_date,
            created_at=follow_up.created_at,
            updated_at=follow_up.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/shortage/arrivals/{arrival_id}/follow-up", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_follow_up(
    *,
    db: Session = Depends(deps.get_db),
    arrival_id: int,
    follow_up_in: ArrivalFollowUpCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建跟催记录
    """
    arrival = db.query(MaterialArrival).filter(MaterialArrival.id == arrival_id).first()
    if not arrival:
        raise HTTPException(status_code=404, detail="到货跟踪不存在")

    follow_up = ArrivalFollowUp(
        arrival_id=arrival_id,
        follow_up_type=follow_up_in.follow_up_type,
        follow_up_note=follow_up_in.follow_up_note,
        followed_by=current_user.id,
        followed_at=datetime.now(),
        supplier_response=follow_up_in.supplier_response,
        next_follow_up_date=follow_up_in.next_follow_up_date
    )

    # 更新到货跟踪的跟催信息
    arrival.follow_up_count = (arrival.follow_up_count or 0) + 1
    arrival.last_follow_up_at = datetime.now()

    db.add(follow_up)
    db.add(arrival)
    db.commit()

    return ResponseModel(code=200, message="跟催记录创建成功")
