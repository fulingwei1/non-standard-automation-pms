# -*- coding: utf-8 -*-
"""生产异常兼容端点。"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import (
    ProductionExceptionCreate,
    ProductionExceptionHandle,
    ProductionExceptionResponse,
)
from app.services.production.exception_service import ProductionExceptionService

router = APIRouter()


@router.get("", response_model=PaginatedResponse)
def read_production_exceptions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    search: Optional[str] = Query(None, description="搜索关键字"),
    exception_type: Optional[str] = Query(None, description="异常类型"),
    exception_level: Optional[str] = Query(None, description="异常级别"),
    status: Optional[str] = Query(None, description="状态"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    work_order_id: Optional[int] = Query(None, description="工单ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = ProductionExceptionService(db)
    return service.list_exceptions(
        pagination,
        search=search,
        exception_type=exception_type,
        exception_level=exception_level,
        status=status,
        project_id=project_id,
        work_order_id=work_order_id,
    )


@router.post("", response_model=ProductionExceptionResponse)
def create_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exception_in: ProductionExceptionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = ProductionExceptionService(db)
    return service.create_exception(exception_in, reporter_id=current_user.id)


@router.get("/{exception_id}", response_model=ProductionExceptionResponse)
def read_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exception_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = ProductionExceptionService(db)
    return service.get_exception(exception_id)


@router.put("/{exception_id}/handle", response_model=ProductionExceptionResponse)
def handle_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exception_id: int,
    handle_in: ProductionExceptionHandle,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = ProductionExceptionService(db)
    return service.handle_exception(exception_id, handle_in, current_user.id)


@router.put("/{exception_id}/resolve", response_model=ProductionExceptionResponse)
def resolve_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exception_id: int,
    handle_in: ProductionExceptionHandle,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = ProductionExceptionService(db)
    return service.resolve_exception(exception_id, handle_in, current_user.id)


@router.put("/{exception_id}/close", response_model=ProductionExceptionResponse)
def close_production_exception(
    *,
    db: Session = Depends(deps.get_db),
    exception_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = ProductionExceptionService(db)
    return service.close_exception(exception_id, current_user.id)
