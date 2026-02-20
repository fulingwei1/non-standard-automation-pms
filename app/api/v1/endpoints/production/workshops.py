# -*- coding: utf-8 -*-
"""
生产管理模块 - 车间管理端点

包含：车间CRUD、产能统计
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import (
    WorkshopCreate,
    WorkshopResponse,
    WorkshopUpdate,
)
from app.services.production.workshop_service import WorkshopService

router = APIRouter()


# ==================== 车间管理 ====================

@router.get("/workshops", response_model=PaginatedResponse)
def read_workshops(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    workshop_type: Optional[str] = Query(None, description="车间类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间列表（机加/装配/调试）
    """
    service = WorkshopService(db)
    return service.list_workshops(
        pagination=pagination,
        workshop_type=workshop_type,
        is_active=is_active,
    )


@router.post("/workshops", response_model=WorkshopResponse)
def create_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_in: WorkshopCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建车间
    """
    service = WorkshopService(db)
    return service.create_workshop(workshop_in)


@router.get("/workshops/{workshop_id}", response_model=WorkshopResponse)
def read_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取车间详情（含产能/人员）
    """
    service = WorkshopService(db)
    return service.get_workshop(workshop_id)


@router.get("/workshops/{workshop_id}/capacity", response_model=dict)
def get_workshop_capacity(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    车间产能统计
    统计车间的产能、实际负荷、利用率等信息
    """
    service = WorkshopService(db)
    return service.get_capacity(
        workshop_id=workshop_id,
        start_date=start_date,
        end_date=end_date,
    )


@router.put("/workshops/{workshop_id}", response_model=WorkshopResponse)
def update_workshop(
    *,
    db: Session = Depends(deps.get_db),
    workshop_id: int,
    workshop_in: WorkshopUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新车间
    """
    service = WorkshopService(db)
    return service.update_workshop(workshop_id, workshop_in)
