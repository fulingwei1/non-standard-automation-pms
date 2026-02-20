# -*- coding: utf-8 -*-
"""
工单管理 - 派工操作
"""
from typing import Any, List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.production import WorkOrderAssignRequest, WorkOrderResponse
from app.services.production.work_order_service import WorkOrderService

router = APIRouter()


@router.put("/work-orders/{order_id}/assign", response_model=WorkOrderResponse)
def assign_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: WorkOrderAssignRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    任务派工（指派人员/工位）
    """
    service = WorkOrderService(db)
    return service.assign_work_order(
        order_id=order_id,
        assign_in=assign_in,
        current_user_id=current_user.id,
    )


@router.post("/work-orders/batch-assign", response_model=ResponseModel)
def batch_assign_work_orders(
    *,
    db: Session = Depends(deps.get_db),
    order_ids: List[int] = Body(..., description="工单ID列表"),
    assign_in: WorkOrderAssignRequest = Body(..., description="派工信息"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量派工
    """
    service = WorkOrderService(db)
    return service.batch_assign(
        order_ids=order_ids,
        assign_in=assign_in,
        current_user_id=current_user.id,
    )
