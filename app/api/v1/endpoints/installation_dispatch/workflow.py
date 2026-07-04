# -*- coding: utf-8 -*-
"""
安装调试派工状态流转端点

所有状态转换均通过 InstallationDispatchStateMachine 执行，确保状态规则统一
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.state_machine.exceptions import (
    InvalidStateTransitionError,
    PermissionDeniedError,
)
from app.core.state_machine.installation_dispatch import InstallationDispatchStateMachine
from app.models.engineer_capacity import EngineerTaskAssignment
from app.models.installation_dispatch import InstallationDispatchOrder
from app.models.timesheet import Timesheet
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


def _dispatch_assignment_no(order_id: int) -> str:
    return f"IDISPATCH-{order_id}"


def _dispatch_planned_end(order: InstallationDispatchOrder):
    estimated_hours = float(order.estimated_hours or 8)
    days = max(1, ceil(estimated_hours / 8))
    return order.scheduled_date + timedelta(days=days - 1)


def _find_dispatch_assignment(db: Session, order_id: int) -> EngineerTaskAssignment | None:
    return (
        db.query(EngineerTaskAssignment)
        .filter(EngineerTaskAssignment.assignment_no == _dispatch_assignment_no(order_id))
        .first()
    )


def _ensure_no_dispatch_conflict(
    db: Session,
    order: InstallationDispatchOrder,
    assigned_to_id: int,
) -> EngineerTaskAssignment | None:
    from app.services.engineer_scheduling_service import EngineerSchedulingService

    service = EngineerSchedulingService(db)
    service.ensure_task_assignment_table()
    existing_assignment = _find_dispatch_assignment(db, order.id)
    planned_end = _dispatch_planned_end(order)
    conflicts = service.detect_task_conflicts(
        assigned_to_id,
        {
            "id": existing_assignment.id if existing_assignment else None,
            "project_id": order.project_id,
            "task_type": order.task_type,
            "planned_start_date": order.scheduled_date,
            "planned_end_date": planned_end,
        },
    )
    if conflicts:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "派工人员存在时间冲突",
                "conflict_count": len(conflicts),
                "conflicts": conflicts,
            },
        )
    return existing_assignment


def _upsert_dispatch_assignment(
    db: Session,
    order: InstallationDispatchOrder,
    assignee: User,
    existing_assignment: EngineerTaskAssignment | None,
) -> None:
    planned_end = _dispatch_planned_end(order)
    assignment = existing_assignment or EngineerTaskAssignment(
        assignment_no=_dispatch_assignment_no(order.id)
    )
    assignment.engineer_id = assignee.id
    assignment.project_id = order.project_id
    assignment.machine_id = order.machine_id
    assignment.task_type = order.task_type
    assignment.task_description = order.task_description or order.task_title
    assignment.estimated_hours = float(order.estimated_hours or 8)
    assignment.planned_start_date = order.scheduled_date
    assignment.planned_end_date = planned_end
    assignment.status = "PENDING"
    assignment.priority = {"URGENT": 100, "HIGH": 80, "NORMAL": 50, "LOW": 20}.get(
        order.priority, 50
    )
    db.add(assignment)


def _ensure_dispatch_assignment(
    db: Session,
    order: InstallationDispatchOrder,
) -> EngineerTaskAssignment | None:
    if not order.assigned_to_id:
        return None
    assignment = _find_dispatch_assignment(db, order.id)
    if assignment:
        return assignment

    assignee = db.query(User).filter(User.id == order.assigned_to_id).first()
    if not assignee:
        return None
    _upsert_dispatch_assignment(db, order, assignee, None)
    db.flush()
    return _find_dispatch_assignment(db, order.id)


def _sync_dispatch_assignment_status(
    db: Session,
    order: InstallationDispatchOrder,
    status_value: str,
) -> EngineerTaskAssignment | None:
    assignment = _ensure_dispatch_assignment(db, order)
    if not assignment:
        return None

    assignment.status = status_value
    if status_value == "IN_PROGRESS":
        assignment.actual_start_date = (order.start_time or datetime.now()).date()
    elif status_value == "COMPLETED":
        assignment.actual_end_date = (order.end_time or datetime.now()).date()
        assignment.actual_hours = float(order.actual_hours or order.estimated_hours or 0)
        if not assignment.actual_start_date and order.start_time:
            assignment.actual_start_date = order.start_time.date()
    elif status_value == "CANCELLED":
        assignment.actual_end_date = datetime.now().date()

    db.add(assignment)
    return assignment


def _upsert_dispatch_timesheet(
    db: Session,
    order: InstallationDispatchOrder,
    assignment: EngineerTaskAssignment | None,
    current_user: User,
) -> Timesheet | None:
    if not order.assigned_to_id:
        return None
    hours = Decimal(str(order.actual_hours or order.estimated_hours or 0))
    if hours <= 0:
        return None

    work_date = (order.end_time.date() if order.end_time else order.scheduled_date)
    timesheet = (
        db.query(Timesheet)
        .filter(
            Timesheet.user_id == order.assigned_to_id,
            Timesheet.task_id == order.id,
            Timesheet.assign_id == (assignment.id if assignment else None),
        )
        .first()
        if assignment
        else None
    )
    if not timesheet:
        timesheet = Timesheet(
            timesheet_no=f"TS-DISPATCH-{order.id}",
            user_id=order.assigned_to_id,
            task_id=order.id,
            assign_id=assignment.id if assignment else None,
            status="DRAFT",
            created_by=current_user.id,
        )

    project = order.project
    assignee = order.assigned_to
    timesheet.user_name = (
        (assignee.real_name or assignee.username)
        if assignee
        else order.assigned_to_name
    )
    timesheet.project_id = order.project_id
    timesheet.project_code = project.project_code if project else None
    timesheet.project_name = project.project_name if project else None
    timesheet.work_date = work_date
    timesheet.hours = hours
    timesheet.overtime_type = "NORMAL"
    timesheet.task_name = order.task_title
    timesheet.work_content = order.task_description or order.task_title
    timesheet.work_result = order.execution_notes or order.solution_provided
    timesheet.progress_before = 0
    timesheet.progress_after = 100
    db.add(timesheet)
    return timesheet


@router.put(
    "/orders/{order_id}/assign",
    response_model=InstallationDispatchOrderResponse,
    status_code=status.HTTP_200_OK,
)
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
    order = (
        db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="安装调试派工单不存在")

    # 验证派工人员是否存在
    assignee = db.query(User).filter(User.id == assign_in.assigned_to_id).first()
    if not assignee:
        raise HTTPException(status_code=404, detail="派工人员不存在")

    existing_assignment = _ensure_no_dispatch_conflict(db, order, assign_in.assigned_to_id)

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
    _upsert_dispatch_assignment(db, order, assignee, existing_assignment)
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
            order = (
                db.query(InstallationDispatchOrder)
                .filter(InstallationDispatchOrder.id == order_id)
                .first()
            )
            if not order:
                failed_orders.append({"order_id": order_id, "reason": "派工单不存在"})
                continue

            try:
                existing_assignment = _ensure_no_dispatch_conflict(
                    db, order, batch_assign_in.assigned_to_id
                )
            except HTTPException as e:
                failed_orders.append({"order_id": order_id, "reason": e.detail})
                continue

            # 使用状态机执行派工
            sm = InstallationDispatchStateMachine(order, db)
            try:
                sm.transition_to(
                    "ASSIGNED",
                    current_user=current_user,
                    comment=batch_assign_in.remark
                    or f"批量派工给 {assignee.real_name or assignee.username}",
                    assigned_to_id=batch_assign_in.assigned_to_id,
                    assigned_to_name=assignee.real_name or assignee.username,
                    assigned_by_id=current_user.id,
                    assigned_by_name=current_user.real_name or current_user.username,
                    remark=batch_assign_in.remark,
                )
                db.add(order)
                _upsert_dispatch_assignment(db, order, assignee, existing_assignment)
                success_count += 1
            except (InvalidStateTransitionError, PermissionDeniedError) as e:
                failed_orders.append({"order_id": order_id, "reason": str(e)})

        except Exception as e:
            failed_orders.append({"order_id": order_id, "reason": str(e)})

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量派工完成：成功 {success_count} 个，失败 {len(failed_orders)} 个",
        data={"success_count": success_count, "failed_orders": failed_orders},
    )


@router.put(
    "/orders/{order_id}/start",
    response_model=InstallationDispatchOrderResponse,
    status_code=status.HTTP_200_OK,
)
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
    order = (
        db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    )
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
    _sync_dispatch_assignment_status(db, order, "IN_PROGRESS")
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.put(
    "/orders/{order_id}/progress",
    response_model=InstallationDispatchOrderResponse,
    status_code=status.HTTP_200_OK,
)
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
    order = (
        db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    )
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


@router.put(
    "/orders/{order_id}/complete",
    response_model=InstallationDispatchOrderResponse,
    status_code=status.HTTP_200_OK,
)
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
    order = (
        db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    )
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
    assignment = _sync_dispatch_assignment_status(db, order, "COMPLETED")
    _upsert_dispatch_timesheet(db, order, assignment, current_user)
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)


@router.put(
    "/orders/{order_id}/cancel",
    response_model=InstallationDispatchOrderResponse,
    status_code=status.HTTP_200_OK,
)
def cancel_installation_dispatch_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.require_permission("installation_dispatch:read")),
) -> Any:
    """
    取消安装调试派工单（通过状态机执行）
    """
    order = (
        db.query(InstallationDispatchOrder).filter(InstallationDispatchOrder.id == order_id).first()
    )
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
    _sync_dispatch_assignment_status(db, order, "CANCELLED")
    db.commit()
    db.refresh(order)

    return read_installation_dispatch_order(order.id, db, current_user)
