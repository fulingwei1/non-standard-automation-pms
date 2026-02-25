# -*- coding: utf-8 -*-
"""
工单管理 - 进度查询
"""
from typing import Any

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.production import WorkOrder
from app.models.user import User
from fastapi import APIRouter

from app.schemas.production import WorkOrderProgressResponse
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/work-orders/{order_id}/progress", response_model=WorkOrderProgressResponse)
def get_work_order_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取工单进度
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    # 计算效率
    efficiency = None
    if order.standard_hours and order.actual_hours and order.actual_hours > 0:
        efficiency = float((order.standard_hours / order.actual_hours) * 100)

    return WorkOrderProgressResponse(
        work_order_id=order.id,
        work_order_no=order.work_order_no,
        task_name=order.task_name,
        plan_qty=order.plan_qty or 0,
        completed_qty=order.completed_qty or 0,
        qualified_qty=order.qualified_qty or 0,
        defect_qty=order.defect_qty or 0,
        progress=order.progress or 0,
        status=order.status,
        plan_start_date=order.plan_start_date,
        plan_end_date=order.plan_end_date,
        actual_start_time=order.actual_start_time,
        actual_end_time=order.actual_end_time,
        standard_hours=float(order.standard_hours) if order.standard_hours else None,
        actual_hours=float(order.actual_hours) if order.actual_hours else 0,
        efficiency=efficiency,
    )
