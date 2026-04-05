# -*- coding: utf-8 -*-
"""生产工人兼容端点。"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import (
    WorkerCreate,
    WorkerPerformanceReportResponse,
    WorkerResponse,
    WorkerUpdate,
)
from app.services.production.worker_service import WorkerService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def read_workers(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    search: Optional[str] = Query(None, description="搜索关键字"),
    workshop_id: Optional[int] = Query(None, description="车间ID"),
    status: Optional[str] = Query(None, description="状态"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = WorkerService(db)
    return service.list_workers(
        pagination,
        search=search,
        workshop_id=workshop_id,
        status=status,
        is_active=is_active,
    )


@router.post("", response_model=WorkerResponse)
def create_worker(
    *,
    db: Session = Depends(deps.get_db),
    worker_in: WorkerCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = WorkerService(db)
    return service.create_worker(worker_in)


@router.get("/{worker_id}", response_model=WorkerResponse)
def read_worker(
    *,
    db: Session = Depends(deps.get_db),
    worker_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = WorkerService(db)
    return service.get_worker(worker_id)


@router.put("/{worker_id}", response_model=WorkerResponse)
def update_worker(
    *,
    db: Session = Depends(deps.get_db),
    worker_id: int,
    worker_in: WorkerUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = WorkerService(db)
    return service.update_worker(worker_id, worker_in)


@router.get("/{worker_id}/performance", response_model=WorkerPerformanceReportResponse)
def get_worker_performance(
    *,
    db: Session = Depends(deps.get_db),
    worker_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = WorkerService(db)
    return service.get_worker_performance(
        worker_id,
        period_start=start_date,
        period_end=end_date,
    )
