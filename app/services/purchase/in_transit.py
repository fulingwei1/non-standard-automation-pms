# -*- coding: utf-8 -*-
"""Shared purchase in-transit quantity helpers."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.purchase import PurchaseOrder, PurchaseOrderItem

PURCHASE_IN_TRANSIT_ORDER_STATUSES = (
    "APPROVED",
    "ORDERED",
    "PARTIAL_RECEIVED",
    "PARTIALLY_RECEIVED",
    "RECEIVING",
    "CONFIRMED",
    "IN_TRANSIT",
    "approved",
    "ordered",
    "partial_received",
    "partially_received",
    "receiving",
    "confirmed",
    "in_transit",
)


def purchase_order_item_remaining_qty():
    return PurchaseOrderItem.quantity - func.coalesce(PurchaseOrderItem.received_qty, 0)


def purchase_in_transit_filters(material_id: int):
    remaining_qty = purchase_order_item_remaining_qty()
    return (
        PurchaseOrderItem.material_id == material_id,
        PurchaseOrder.status.in_(PURCHASE_IN_TRANSIT_ORDER_STATUSES),
        remaining_qty > 0,
    )


def get_purchase_in_transit_qty(db: Session, material_id: Optional[int]) -> Decimal:
    if not material_id:
        return Decimal("0")

    remaining_qty = purchase_order_item_remaining_qty()
    result = (
        db.query(func.sum(remaining_qty))
        .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
        .filter(*purchase_in_transit_filters(material_id))
        .scalar()
    )
    return result or Decimal("0")
