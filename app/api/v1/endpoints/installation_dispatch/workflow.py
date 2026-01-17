# -*- coding: utf-8 -*-
"""
安装调试派工状态流转端点
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.project import Machine
from app.models.service import ServiceRecord
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.installation_dispatch import (
    InstallationDispatchOrderAssign,
    InstallationDispatchOrderBatchAssign,
    InstallationDispatchOrderComplete,
    InstallationDispatchOrderProgress,
    InstallationDispatchOrderResponse,
    InstallationDispatchOrderStart,
)

from .orders import read_installation_dispatch_order

router = APIRouter()


@router.put("/orders/{order_id}/assign", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def assign_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: InstallationDispatchOrderAssign,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    派工安装调试派工单
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.status != "PENDING":
        raise HTTPException(status_code=400, detail="只有待派工状态的派工单才能派工")

    # 验证派工人员是否存在
    assignee = db.query(User).filter(User.id == assign_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="派工人员不存在")

    order.assigned_to_id = assign_in.assigned_to_id
    order.assigned_to_name = assignee.real_name or assignee.username
    order.assigned_by_id = current_user.id
    order.assigned_by_name = current_user.real_name or current_user.username
    order.assigned_time = datetime.now()
    order.status = "ASSIGNED"
    if assign_in.remark:
        order.remark = (order.remark or "") + f"\n派工备注：{assign_in.remark}"

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.post("/orders/batch-assign", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_assign_installation_dispatch_orders(
    *,
    db: Session = Depends(deps.get_db),
    batch_assign_in: InstallationDispatchOrderBatchAssign,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    批量派工安装调试派工单
    """
    # 验证派工人员是否存在
    assignee = db.query(User).filter(User.id == batch_assign_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="派工人员不存在")

    success_count = 0
    failed_orders = []

    for order_id in batch_assign_in.order_ids:
        try:
            order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
            if not order:
                failed_orders.append({"order_id": order_id, "reason": "派工单不存在"})
                continue

            if order.status != "PENDING":
                failed_orders.append({"order_id": order_id, "reason": f"派工单状态为{order.status}，不能派工"})
                continue

            order.assigned_to_id = batch_assign_in.assigned_to_id
            order.assigned_to_name = assignee.real_name or assignee.username
            order.assigned_by_id = current_user.id
            order.assigned_by_name = current_user.real_name or current_user.username
            order.assigned_time = datetime.now()
            order.status = "ASSIGNED"
            if batch_assign_in.remark:
                order.remark = (order.remark or "") + f"\n批量派工备注：{batch_assign_in.remark}"

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


@router.put("/orders/{order_id}/start", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def start_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: InstallationDispatchOrderStart,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    开始安装调试任务
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.status != "ASSIGNED":
        raise HTTPException(status_code=400, detail="只有已派工状态的派工单才能开始")

    if order.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能开始分配给自己的任务")

    order.status = "IN_PROGRESS"
    order.start_time = start_in.start_time or datetime.now()
    order.progress = 0

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.put("/orders/{order_id}/progress", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def update_installation_dispatch_order_progress(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    progress_in: InstallationDispatchOrderProgress,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    更新安装调试任务进度
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只有进行中状态的派工单才能更新进度")

    order.progress = progress_in.progress
    if progress_in.execution_notes:
        order.execution_notes = (order.execution_notes or "") + f"\n{datetime.now().strftime('%Y-%m-%d %H:%M')}：{progress_in.execution_notes}"

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.put("/orders/{order_id}/complete", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def complete_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    complete_in: InstallationDispatchOrderComplete,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    完成安装调试任务
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只有进行中状态的派工单才能完成")

    order.status = "COMPLETED"
    order.end_time = complete_in.end_time or datetime.now()
    order.actual_hours = complete_in.actual_hours
    order.progress = 100

    if complete_in.execution_notes:
        order.execution_notes = (order.execution_notes or "") + f"\n完成说明：{complete_in.execution_notes}"
    if complete_in.issues_found:
        order.issues_found = complete_in.issues_found
    if complete_in.solution_provided:
        order.solution_provided = complete_in.solution_provided
    if complete_in.photos:
        order.photos = complete_in.photos

    # 自动创建现场服务记录
    try:
        from app.api.v1.endpoints.service import generate_record_no

        # 获取机台号
        machine_no = None
        if order.machine_id:
            machine = db.query(Machine).filter(Machine.id == order.machine_id).first()
            if machine:
                machine_no = machine.machine_no

        service_record = ServiceRecord(
            record_no=generate_record_no(db),
            service_type="INSTALLATION",
            project_id=order.project_id,
            machine_no=machine_no,
            customer_id=order.customer_id,
            location=order.location,
            service_date=order.scheduled_date,
            start_time=order.start_time.strftime("%H:%M") if order.start_time else None,
            end_time=order.end_time.strftime("%H:%M") if order.end_time else None,
            duration_hours=complete_in.actual_hours or order.estimated_hours,
            service_engineer_id=order.assigned_to_id,
            service_engineer_name=order.assigned_to_name,
            customer_contact=order.customer_contact,
            customer_phone=order.customer_phone,
            service_content=order.task_description or order.task_title,
            service_result=complete_in.execution_notes,
            issues_found=complete_in.issues_found,
            solution_provided=complete_in.solution_provided,
            photos=complete_in.photos,
            status="COMPLETED",
        )
        db.add(service_record)
        db.flush()
        order.service_record_id = service_record.id
    except Exception as e:
        # 如果创建服务记录失败，不影响派工单完成
        logging.warning(f"自动创建现场服务记录失败：{str(e)}")

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.put("/orders/{order_id}/cancel", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def cancel_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    取消安装调试派工单
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.status in ["COMPLETED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="已完成或已取消的派工单不能再次取消")

    order.status = "CANCELLED"

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)
