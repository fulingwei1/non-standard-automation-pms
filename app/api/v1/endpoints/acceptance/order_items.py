# -*- coding: utf-8 -*-
"""
验收单管理 - 检查项管理

包含检查项列表获取、结果更新
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder, AcceptanceOrderItem
from app.models.user import User
from app.schemas.acceptance import (
    CheckItemResultResponse,
    CheckItemResultUpdate,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/acceptance-orders/{order_id}/items", response_model=List[CheckItemResultResponse], status_code=status.HTTP_200_OK)
def read_acceptance_order_items(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收检查项列表
    """
    get_or_404(db, AcceptanceOrder, order_id, "验收单不存在")

    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order_id).order_by(
        AcceptanceOrderItem.category_code, AcceptanceOrderItem.sort_order
    ).all()

    items_data = []
    for item in items:
        checked_by_name = None
        if item.checked_by:
            user = db.query(User).filter(User.id == item.checked_by).first()
            checked_by_name = user.real_name or user.username if user else None

        items_data.append(CheckItemResultResponse(
            id=item.id,
            category_code=item.category_code,
            category_name=item.category_name,
            item_code=item.item_code,
            item_name=item.item_name,
            check_method=item.check_method,
            acceptance_criteria=item.acceptance_criteria,
            standard_value=item.standard_value,
            tolerance_min=item.tolerance_min,
            tolerance_max=item.tolerance_max,
            unit=item.unit,
            is_required=item.is_required,
            is_key_item=item.is_key_item,
            result_status=item.result_status,
            actual_value=item.actual_value,
            deviation=item.deviation,
            remark=item.remark,
            checked_by=item.checked_by,
            checked_by_name=checked_by_name,
            checked_at=item.checked_at,
            created_at=item.created_at.isoformat() if item.created_at else None,
            updated_at=item.updated_at.isoformat() if item.updated_at else None
        ))

    return items_data


@router.put("/acceptance-items/{item_id}", response_model=CheckItemResultResponse, status_code=status.HTTP_200_OK)
def update_check_item_result(
    *,
    db: Session = Depends(deps.get_db),
    item_id: int,
    result_in: CheckItemResultUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新检查项结果
    """
    item = get_or_404(db, AcceptanceOrderItem, item_id, "检查项不存在")

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == item.order_id).first()
    if order.status != "IN_PROGRESS":
        raise HTTPException(status_code=400, detail="只能更新进行中验收单的检查项")

    # 更新检查项结果
    item.result_status = result_in.result_status
    item.actual_value = result_in.actual_value
    item.deviation = result_in.deviation
    item.remark = result_in.remark
    item.checked_by = current_user.id
    item.checked_at = datetime.now()

    db.add(item)

    # 更新验收单统计（支持有条件通过的权重计算）
    items = db.query(AcceptanceOrderItem).filter(AcceptanceOrderItem.order_id == order.id).all()
    passed = len([i for i in items if i.result_status == "PASSED"])
    failed = len([i for i in items if i.result_status == "FAILED"])
    na = len([i for i in items if i.result_status == "NA"])
    conditional = len([i for i in items if i.result_status == "CONDITIONAL"])
    # 不适用(NA)的项不计入总数
    total = len([i for i in items if i.result_status != "PENDING" and i.result_status != "NA"])

    order.passed_items = passed
    order.failed_items = failed
    order.na_items = na
    order.total_items = len(items)

    # 通过率计算：通过数 + 有条件通过数*0.8
    if total > 0:
        # 有条件通过按0.8权重计算
        effective_passed = passed + conditional * Decimal("0.8")
        order.pass_rate = Decimal(str((effective_passed / total) * 100)).quantize(Decimal("0.01"))
    else:
        order.pass_rate = Decimal("0")

    db.add(order)
    db.commit()
    db.refresh(item)

    # 获取检查人姓名
    checked_by_name = None
    if item.checked_by:
        user = db.query(User).filter(User.id == item.checked_by).first()
        checked_by_name = user.real_name or user.username if user else None

    return CheckItemResultResponse(
        id=item.id,
        category_code=item.category_code,
        category_name=item.category_name,
        item_code=item.item_code,
        item_name=item.item_name,
        check_method=item.check_method,
        acceptance_criteria=item.acceptance_criteria,
        standard_value=item.standard_value,
        tolerance_min=item.tolerance_min,
        tolerance_max=item.tolerance_max,
        unit=item.unit,
        is_required=item.is_required,
        is_key_item=item.is_key_item,
        result_status=item.result_status,
        actual_value=item.actual_value,
        deviation=item.deviation,
        remark=item.remark,
        checked_by=item.checked_by,
        checked_by_name=checked_by_name,
        checked_at=item.checked_at,
        created_at=item.created_at,
        updated_at=item.updated_at
    )
