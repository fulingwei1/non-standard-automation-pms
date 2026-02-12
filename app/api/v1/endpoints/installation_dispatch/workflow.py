# -*- coding: utf-8 -*-
"""
安装调试派工状态流转端点

所有状态转换均通过 InstallationDispatchStateMachine 执行，确保状态规则统一
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.installation_dispatch import InstallationDispatchStateMachine
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
)
from app.models.installation_dispatch import InstallationDispatchOrder
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
logger = logging.getLogger(__name__)


@router.put("/orders/{order_id}/assign", response_model=InstallationDispatchOrderResponse, status_code=status.HTTP_200_OK)
def assign_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    assign_in: InstallationDispatchOrderAssign,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    派工安装调试派工单（通过状态机执行）
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    # 验证派工人员是否存在
    assignee = db.query(User).filter(User.id == assign_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="派工人员不存在")

    # 使用状态机执行派工
    sm = InstallationDispatchStateMachine(order, db)
    try:
        sm.transition_to(
            "ASSIGNED",
            current_user=current_user,
            comment=assign_in.remark or f"派工给 {assignee.real_name or assignee.username}",
            assigned_to_id=assign_in.assigned_to_id,
            assigned_to_name=assignee.real_name or assignee.username,
            assigned_by_id=current_user.id,
            assigned_by_name=current_user.real_name or current_user.username,
            remark=assign_in.remark,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

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
    批量派工安装调试派工单（通过状态机执行）
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

            # 使用状态机执行派工
            sm = InstallationDispatchStateMachine(order, db)
            try:
                sm.transition_to(
                    "ASSIGNED",
                    current_user=current_user,
                    comment=batch_assign_in.remark or f"批量派工给 {assignee.real_name or assignee.username}",
                    assigned_to_id=batch_assign_in.assigned_to_id,
                    assigned_to_name=assignee.real_name or assignee.username,
                    assigned_by_id=current_user.id,
                    assigned_by_name=current_user.real_name or current_user.username,
                    remark=batch_assign_in.remark,
                )
                db.add(order)
                success_count += 1
            except (InvalidStateTransitionError, PermissionDeniedError) as e:
                failed_orders.append({"order_id": order_id, "reason": str(e)})

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
    开始安装调试任务（通过状态机执行）
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    if order.assigned_to_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能开始分配给自己的任务")

    # 使用状态机执行开始
    sm = InstallationDispatchStateMachine(order, db)
    try:
        sm.transition_to(
            "IN_PROGRESS",
            current_user=current_user,
            comment="开始执行安装调试任务",
            start_time=start_in.start_time or datetime.now(),
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

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
    更新安装调试任务进度（不改变状态，使用状态机辅助方法）
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    # 使用状态机的 update_progress 方法（不涉及状态转换）
    sm = InstallationDispatchStateMachine(order, db)
    try:
        sm.update_progress(
            progress=progress_in.progress,
            notes=progress_in.execution_notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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
    完成安装调试任务（通过状态机执行，自动创建服务记录）
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    # 使用状态机执行完成（状态机内部会自动创建服务记录）
    sm = InstallationDispatchStateMachine(order, db)
    try:
        sm.transition_to(
            "COMPLETED",
            current_user=current_user,
            comment=complete_in.execution_notes or "完成安装调试任务",
            end_time=complete_in.end_time or datetime.now(),
            actual_hours=complete_in.actual_hours,
            execution_notes=complete_in.execution_notes,
            issues_found=complete_in.issues_found,
            solution_provided=complete_in.solution_provided,
            photos=complete_in.photos,
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

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
    取消安装调试派工单（通过状态机执行）
    """
    order = db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    # 状态机根据当前状态选择对应的取消转换
    sm = InstallationDispatchStateMachine(order, db)
    try:
        sm.transition_to(
            "CANCELLED",
            current_user=current_user,
            comment="取消安装调试派工单",
        )
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)

