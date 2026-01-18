# -*- coding: utf-8 -*-
"""
验收单管理 - 工作流操作

包含提交、开始、完成验收等流程控制
"""

import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceOrderComplete,
    AcceptanceOrderResponse,
    AcceptanceOrderStart,
)
from app.schemas.common import ResponseModel

from .order_crud import read_acceptance_order
from .utils import validate_completion_rules, validate_edit_rules

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/acceptance-orders/{order_id}/submit", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def submit_acceptance_order(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    提交验收单（草稿→待验收）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    # AR006: 客户签字后验收单不可修改
    validate_edit_rules(db, order_id)

    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能提交草稿状态的验收单")

    if order.total_items == 0:
        raise HTTPException(status_code=400, detail="验收单没有检查项，无法提交")

    order.status = "PENDING"

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)


@router.put("/acceptance-orders/{order_id}/start", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def start_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    start_in: AcceptanceOrderStart,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    开始验收（待验收→验收中）
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status not in ["DRAFT", "PENDING"]:
        raise HTTPException(status_code=400, detail="只能开始草稿或待验收状态的验收单")

    if order.total_items == 0:
        raise HTTPException(status_code=400, detail="验收单没有检查项，无法开始验收")

    order.status = "IN_PROGRESS"
    order.actual_start_date = datetime.now()
    if start_in.location:
        order.location = start_in.location

    db.add(order)
    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)


@router.put("/acceptance-orders/{order_id}/complete", response_model=AcceptanceOrderResponse, status_code=status.HTTP_200_OK)
def complete_acceptance(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    complete_in: AcceptanceOrderComplete,
    auto_trigger_invoice: bool = Query(True, description="自动触发开票"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    完成验收（自动触发收款计划开票）
    """
    from app.services.acceptance_completion_service import (
        check_auto_stage_transition_after_acceptance,
        handle_acceptance_status_transition,
        handle_progress_integration,
        trigger_bonus_calculation,
        trigger_invoice_on_acceptance,
        trigger_warranty_period,
        update_acceptance_order_status,
        validate_required_check_items,
    )

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能完成进行中状态的验收单")

    # AR005: 检查是否所有必检项都已检查
    validate_required_check_items(db, order_id)

    # AR004: 检查是否存在未闭环的阻塞问题
    validate_completion_rules(db, order_id)

    # 更新验收单状态
    update_acceptance_order_status(
        db,
        order,
        complete_in.overall_result,
        complete_in.conclusion,
        complete_in.conditions
    )

    # Issue 7.4: 如果验收通过，检查是否有绑定的收款计划，自动触发开票
    if auto_trigger_invoice and complete_in.overall_result == "PASSED":
        trigger_invoice_on_acceptance(db, order_id, auto_trigger_invoice)

    # Sprint 2.2: 验收管理状态联动（FAT/SAT）
    handle_acceptance_status_transition(db, order, complete_in.overall_result)

    # 验收联动：处理验收结果对进度跟踪的影响
    handle_progress_integration(db, order, complete_in.overall_result)

    # Issue 1.2: FAT/SAT验收通过后自动触发阶段流转检查
    check_auto_stage_transition_after_acceptance(db, order, complete_in.overall_result)

    # AR007: 如果终验收通过，自动触发质保期
    trigger_warranty_period(db, order, complete_in.overall_result)

    # 如果验收通过，自动触发奖金计算
    trigger_bonus_calculation(db, order, complete_in.overall_result)

    db.commit()
    db.refresh(order)

    return read_acceptance_order(order_id, db, current_user)
