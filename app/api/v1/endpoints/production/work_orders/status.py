# -*- coding: utf-8 -*-
"""
工单管理 - 状态操作
"""
from datetime import datetime
from typing import Any, Optional

from fastapi import Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.production import WorkOrder, Workstation
from app.models.user import User
from app.schemas.production import WorkOrderResponse

from fastapi import APIRouter

from .utils import get_work_order_response

router = APIRouter()


@router.put("/work-orders/{order_id}/start", response_model=WorkOrderResponse)
def start_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工的工单才能开始")

    order.status = "STARTED"
    order.actual_start_time = datetime.now()

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status not in ["STARTED", "PAUSED"]:
        raise HTTPException(status_code=400, detail="只有已开始或已暂停的工单才能完成")

    order.status = "COMPLETED"
    order.actual_end_time = datetime.now()
    order.progress = 100

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/pause", response_model=WorkOrderResponse)
def pause_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    pause_reason: Optional[str] = Body(None, description="暂停原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    暂停工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "STARTED":
        raise HTTPException(status_code=400, detail="只有已开始的工单才能暂停")

    order.status = "PAUSED"
    if pause_reason:
        order.remark = (order.remark or "") + f"\n暂停原因：{pause_reason}"

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/resume", response_model=WorkOrderResponse)
def resume_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    恢复工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status != "PAUSED":
        raise HTTPException(status_code=400, detail="只有已暂停的工单才能恢复")

    order.status = "STARTED"

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "WORKING"
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return get_work_order_response(db, order)


@router.put("/work-orders/{order_id}/cancel", response_model=WorkOrderResponse)
def cancel_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    cancel_reason: Optional[str] = Body(None, description="取消原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消工单
    """
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")

    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="已完成或已取消的工单不能再次取消")

    order.status = "CANCELLED"
    if cancel_reason:
        order.remark = (order.remark or "") + f"\n取消原因：{cancel_reason}"

    # 更新工位状态
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            workstation.status = "IDLE"
            workstation.current_work_order_id = None
            workstation.current_worker_id = None
            db.add(workstation)

    db.add(order)
    db.commit()
    db.refresh(order)

    return get_work_order_response(db, order)
