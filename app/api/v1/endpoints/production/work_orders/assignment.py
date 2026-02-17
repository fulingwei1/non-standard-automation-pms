# -*- coding: utf-8 -*-
"""
工单管理 - 派工操作
"""
from datetime import datetime
from typing import Any, List

from fastapi import Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.production import Worker, WorkOrder, Workstation
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.production import WorkOrderAssignRequest, WorkOrderResponse

from fastapi import APIRouter

from .utils import get_work_order_response
from app.utils.db_helpers import get_or_404, save_obj

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
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待派工状态的工单才能派工")

    # 检查工人是否存在
    worker = get_or_404(db, Worker, assign_in.assigned_to, "工人不存在")

    # 检查工位是否存在
    if assign_in.workstation_id:
        workstation = get_or_404(db, Workstation, assign_in.workstation_id, "工位不存在")
        if order.workshop_id and workstation.workshop_id != order.workshop_id:
            raise HTTPException(status_code=400, detail="工位不属于该车间")

    order.assigned_to = assign_in.assigned_to
    order.assigned_at = datetime.now()
    order.assigned_by = current_user.id
    order.status = "ASSIGNED"

    if assign_in.workstation_id:
        order.workstation_id = assign_in.workstation_id

    save_obj(db, order)

    return get_work_order_response(db, order)


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
    success_count = 0
    failed_orders = []

    for order_id in order_ids:
        try:
            order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
            if not order:
                failed_orders.append({"order_id": order_id, "reason": "工单不存在"})
                continue

            if order.status != "PENDING":
                failed_orders.append({"order_id": order_id, "reason": f"工单状态为{order.status}，不能派工"})
                continue

            # 验证工人
            if assign_in.assigned_to:
                worker = db.query(Worker).filter(Worker.id == assign_in.assigned_to).first()
                if not worker:
                    failed_orders.append({"order_id": order_id, "reason": "工人不存在"})
                    continue
                order.assigned_to = assign_in.assigned_to
                order.assigned_to_name = worker.worker_name

            # 验证工位
            if assign_in.workstation_id:
                workstation = db.query(Workstation).filter(Workstation.id == assign_in.workstation_id).first()
                if not workstation:
                    failed_orders.append({"order_id": order_id, "reason": "工位不存在"})
                    continue
                order.workstation_id = assign_in.workstation_id

            order.status = "ASSIGNED"
            order.assigned_at = datetime.now()
            order.assigned_by = current_user.id

            db.add(order)
            success_count += 1
        except Exception as e:
            failed_orders.append({"order_id": order_id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量派工完成：成功 {success_count} 个，失败 {len(failed_orders)} 个",
        data={"success_count": success_count, "failed_orders": failed_orders}
    )
