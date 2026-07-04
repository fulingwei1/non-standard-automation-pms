# -*- coding: utf-8 -*-
"""Purchase order status machine helpers."""

from typing import Dict, List

from app.models.purchase import PurchaseOrder


PURCHASE_ORDER_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["SUBMITTED", "PENDING_APPROVAL", "CANCELLED"],
    "REJECTED": ["DRAFT", "SUBMITTED", "PENDING_APPROVAL", "CANCELLED"],
    "SUBMITTED": ["APPROVED", "REJECTED", "DRAFT", "CANCELLED"],
    "PENDING_APPROVAL": ["APPROVED", "REJECTED", "DRAFT", "CANCELLED"],
    "APPROVED": ["ORDERED", "CANCELLED"],
    "ORDERED": ["PARTIAL_RECEIVED", "CANCELLED"],
    "PARTIAL_RECEIVED": ["PARTIAL_RECEIVED", "RECEIVED", "CANCELLED"],
    "RECEIVED": ["CLOSED"],
    "CLOSED": [],
    "CANCELLED": [],
}


def validate_purchase_order_transition(current_status: str, target_status: str) -> None:
    """Validate a purchase order status transition."""
    if current_status == target_status:
        raise ValueError(f"采购订单当前状态已经是 '{current_status}'，无需重复操作。")

    allowed = PURCHASE_ORDER_TRANSITIONS.get(current_status)
    if allowed is None:
        raise ValueError(f"未知的采购订单状态 '{current_status}'，无法执行状态转换。")

    if target_status not in allowed:
        if allowed:
            allowed_str = "、".join(allowed)
            raise ValueError(
                f"采购订单当前状态为 '{current_status}'，不允许转换到 '{target_status}'。"
                f"当前状态可转换到：{allowed_str}。"
            )
        raise ValueError(f"采购订单当前状态为 '{current_status}'（终态），不允许任何状态转换。")


def transition_purchase_order_status(
    order: PurchaseOrder,
    target_status: str,
) -> PurchaseOrder:
    """Validate and apply a purchase order status transition."""
    validate_purchase_order_transition(order.status, target_status)
    order.status = target_status
    return order
