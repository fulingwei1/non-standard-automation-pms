# -*- coding: utf-8 -*-
"""
工单管理 - 状态操作

使用统一状态更新服务重构
"""
import logging
from typing import Any, Optional

from fastapi import Body, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.production import WorkOrder, Workstation
from app.models.user import User
from app.schemas.production import WorkOrderResponse
from app.services.status_update_service import StatusUpdateService

from fastapi import APIRouter

from .utils import get_work_order_response
from app.utils.db_helpers import get_or_404

logger = logging.getLogger(__name__)
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

    使用统一状态更新服务，支持：
    - 状态转换规则验证（只能从ASSIGNED转换到STARTED）
    - 自动记录开始时间
    - 关联工位状态更新
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    # 准备关联实体更新（工位）
    related_entities = []
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            related_entities.append({
                "entity": workstation,
                "field": "status",
                "value": "WORKING",
            })
            # 工位还需要更新其他字段
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=order,
        new_status="STARTED",
        operator=current_user,
        transition_rules={
            "ASSIGNED": ["STARTED"],  # 只能从ASSIGNED转换到STARTED
        },
        timestamp_fields={
            "STARTED": "actual_start_time",
        },
        related_entities=related_entities,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "开始工单失败",
        )

    return get_work_order_response(db, result.entity)


@router.put("/work-orders/{order_id}/complete", response_model=WorkOrderResponse)
def complete_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成工单

    使用统一状态更新服务，支持：
    - 状态转换规则验证（只能从STARTED或PAUSED转换到COMPLETED）
    - 自动记录完成时间
    - 自动设置进度为100%
    - 关联工位状态更新
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    # 准备关联实体更新（工位）
    related_entities = []
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            related_entities.append({
                "entity": workstation,
                "field": "status",
                "value": "IDLE",
            })
            # 工位还需要清空其他字段
            workstation.current_work_order_id = None
            workstation.current_worker_id = None

    # 更新前回调：设置进度
    def before_update_callback(entity, old_status, new_status, operator):
        entity.progress = 100

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=order,
        new_status="COMPLETED",
        operator=current_user,
        transition_rules={
            "STARTED": ["COMPLETED"],
            "PAUSED": ["COMPLETED"],
        },
        timestamp_fields={
            "COMPLETED": "actual_end_time",
        },
        related_entities=related_entities,
        before_update_callback=before_update_callback,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "完成工单失败",
        )

    return get_work_order_response(db, result.entity)


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

    使用统一状态更新服务，支持：
    - 状态转换规则验证（只能从STARTED转换到PAUSED）
    - 记录暂停原因
    - 关联工位状态更新
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    # 准备关联实体更新（工位）
    related_entities = []
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            related_entities.append({
                "entity": workstation,
                "field": "status",
                "value": "IDLE",
            })

    # 更新前回调：记录暂停原因
    def before_update_callback(entity, old_status, new_status, operator):
        if pause_reason:
            entity.remark = (entity.remark or "") + f"\n暂停原因：{pause_reason}"

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=order,
        new_status="PAUSED",
        operator=current_user,
        transition_rules={
            "STARTED": ["PAUSED"],  # 只能从STARTED转换到PAUSED
        },
        related_entities=related_entities,
        before_update_callback=before_update_callback,
        reason=pause_reason,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "暂停工单失败",
        )

    return get_work_order_response(db, result.entity)


@router.put("/work-orders/{order_id}/resume", response_model=WorkOrderResponse)
def resume_work_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    恢复工单

    使用统一状态更新服务，支持：
    - 状态转换规则验证（只能从PAUSED转换到STARTED）
    - 关联工位状态更新
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    # 准备关联实体更新（工位）
    related_entities = []
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            related_entities.append({
                "entity": workstation,
                "field": "status",
                "value": "WORKING",
            })
            # 工位还需要更新其他字段
            workstation.current_work_order_id = order.id
            workstation.current_worker_id = order.assigned_to

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=order,
        new_status="STARTED",
        operator=current_user,
        transition_rules={
            "PAUSED": ["STARTED"],  # 只能从PAUSED转换到STARTED
        },
        related_entities=related_entities,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "恢复工单失败",
        )

    return get_work_order_response(db, result.entity)


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

    使用统一状态更新服务，支持：
    - 状态转换规则验证（不能从COMPLETED或CANCELLED转换）
    - 记录取消原因
    - 关联工位状态更新
    """
    order = get_or_404(db, WorkOrder, order_id, detail="工单不存在")

    # 准备关联实体更新（工位）
    related_entities = []
    if order.workstation_id:
        workstation = db.query(Workstation).filter(Workstation.id == order.workstation_id).first()
        if workstation:
            related_entities.append({
                "entity": workstation,
                "field": "status",
                "value": "IDLE",
            })
            # 工位还需要清空其他字段
            workstation.current_work_order_id = None
            workstation.current_worker_id = None

    # 更新前回调：记录取消原因
    def before_update_callback(entity, old_status, new_status, operator):
        if cancel_reason:
            entity.remark = (entity.remark or "") + f"\n取消原因：{cancel_reason}"

    # 使用统一状态更新服务
    service = StatusUpdateService(db)
    result = service.update_status(
        entity=order,
        new_status="CANCELLED",
        operator=current_user,
        transition_rules={
            # 允许从除COMPLETED和CANCELLED外的所有状态转换到CANCELLED
            "ASSIGNED": ["CANCELLED"],
            "STARTED": ["CANCELLED"],
            "PAUSED": ["CANCELLED"],
        },
        related_entities=related_entities,
        before_update_callback=before_update_callback,
        reason=cancel_reason,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail="; ".join(result.errors) if result.errors else "取消工单失败",
        )

    return get_work_order_response(db, result.entity)
