# -*- coding: utf-8 -*-
"""
工单管理 - CRUD操作
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.production import WorkOrderCreate, WorkOrderResponse
from app.services.production.work_order_service import WorkOrderService

router = APIRouter()


@router.get("/work-orders", response_model=PaginatedResponse)
def read_work_orders(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    workshop_id: Optional[int] = Query(None, description="车间ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    assigned_to: Optional[int] = Query(None, description="指派给筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单列表（分页+筛选）
    """
    service = WorkOrderService(db)
    return service.list_work_orders(
        pagination=pagination,
        project_id=project_id,
        workshop_id=workshop_id,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
    )


@router.post("/work-orders", response_model=WorkOrderResponse)
def create_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_in: WorkOrderCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建工单
    """
    service = WorkOrderService(db)
    return service.create_work_order(order_in, current_user_id=current_user.id)


@router.get("/work-orders/{order_id}", response_model=WorkOrderResponse)
def read_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单详情
    """
    service = WorkOrderService(db)
    return service.get_work_order(order_id)
