# -*- coding: utf-8 -*-
"""
外协交付 - 自动生成
从 outsourcing.py 拆分
"""

# -*- coding: utf-8 -*-
"""
外协管理 API endpoints
包含：外协供应商、外协订单、交付与质检、进度与付款
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

logger = logging.getLogger(__name__)
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.outsourcing import (
    OutsourcingDelivery,
    OutsourcingDeliveryItem,
    OutsourcingOrder,
    OutsourcingOrderItem,
)
from app.models.user import User
from app.models.vendor import Vendor
from app.schemas.common import PaginatedResponse
from app.schemas.outsourcing import (
    OutsourcingDeliveryCreate,
    OutsourcingDeliveryResponse,
)

router = APIRouter()

from app.common.query_filters import apply_pagination

# 使用统一的编码生成工具
from app.utils.domain_codes import outsourcing as outsourcing_codes

generate_order_no = outsourcing_codes.generate_order_no
generate_delivery_no = outsourcing_codes.generate_delivery_no
generate_inspection_no = outsourcing_codes.generate_inspection_no


def _decimal_or_zero(value: Any) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value or "0"))


def _vendor_name_or_default(vendor: Optional[Vendor]) -> str:
    return vendor.supplier_name if vendor and vendor.supplier_name else "未知外协商"


def _build_delivery_response(db: Session, delivery: OutsourcingDelivery) -> OutsourcingDeliveryResponse:
    vendor = db.query(Vendor).filter(Vendor.id == delivery.vendor_id).first()
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()

    return OutsourcingDeliveryResponse(
        id=delivery.id,
        delivery_no=delivery.delivery_no,
        order_id=delivery.order_id,
        order_no=order.order_no if order else None,
        vendor_name=_vendor_name_or_default(vendor),
        delivery_date=delivery.delivery_date,
        delivery_type=delivery.delivery_type,
        status=delivery.status,
        received_at=delivery.received_at,
        created_at=delivery.created_at,
        updated_at=delivery.updated_at,
    )


def _delivery_items_for_order(db: Session, order_id: int) -> list[OutsourcingDeliveryItem]:
    return (
        db.query(OutsourcingDeliveryItem)
        .join(OutsourcingDelivery, OutsourcingDelivery.id == OutsourcingDeliveryItem.delivery_id)
        .filter(OutsourcingDelivery.order_id == order_id)
        .all()
    )


def _sync_order_receipt_status(db: Session, order: OutsourcingOrder) -> None:
    order_items = (
        db.query(OutsourcingOrderItem)
        .filter(OutsourcingOrderItem.order_id == order.id)
        .all()
    )
    delivery_items = _delivery_items_for_order(db, order.id)
    deliveries = (
        db.query(OutsourcingDelivery)
        .filter(OutsourcingDelivery.order_id == order.id)
        .all()
    )

    delivered_by_item: dict[int, Decimal] = {}
    received_by_item: dict[int, Decimal] = {}
    for delivery_item in delivery_items:
        order_item_id = delivery_item.order_item_id
        delivered_by_item[order_item_id] = delivered_by_item.get(
            order_item_id, Decimal("0")
        ) + _decimal_or_zero(delivery_item.delivery_quantity)
        received_by_item[order_item_id] = received_by_item.get(
            order_item_id, Decimal("0")
        ) + _decimal_or_zero(delivery_item.received_quantity)

    for order_item in order_items:
        delivered_qty = delivered_by_item.get(order_item.id, Decimal("0"))
        received_qty = received_by_item.get(order_item.id, Decimal("0"))
        ordered_qty = _decimal_or_zero(order_item.quantity)
        order_item.delivered_quantity = delivered_qty
        if received_qty >= ordered_qty:
            order_item.status = "RECEIVED"
        elif received_qty > Decimal("0"):
            order_item.status = "PARTIAL_RECEIVED"
        db.add(order_item)

    fully_received = bool(order_items) and all(
        received_by_item.get(order_item.id, Decimal("0")) >= _decimal_or_zero(order_item.quantity)
        for order_item in order_items
    )
    all_deliveries_received = bool(deliveries) and all(
        delivery.status == "RECEIVED" for delivery in deliveries
    )

    if fully_received and all_deliveries_received:
        order.status = "RECEIVED"
        order.actual_date = max(
            (delivery.delivery_date for delivery in deliveries if delivery.delivery_date),
            default=order.actual_date,
        )
    elif deliveries:
        order.status = "IN_PROGRESS"
    db.add(order)


def _validate_delivery_items(
    db: Session, delivery_in: OutsourcingDeliveryCreate
) -> list[tuple[Any, OutsourcingOrderItem]]:
    validated_items: list[tuple[Any, OutsourcingOrderItem]] = []
    requested_by_item: dict[int, Decimal] = {}

    for item_in in delivery_in.items:
        order_item = (
            db.query(OutsourcingOrderItem)
            .filter(OutsourcingOrderItem.id == item_in.order_item_id)
            .first()
        )
        if not order_item or order_item.order_id != delivery_in.order_id:
            raise HTTPException(
                status_code=400, detail=f"订单明细ID {item_in.order_item_id} 不存在或不属于该订单"
            )

        already_requested = requested_by_item.get(order_item.id, Decimal("0"))
        remaining_qty = (
            _decimal_or_zero(order_item.quantity)
            - _decimal_or_zero(order_item.delivered_quantity)
            - already_requested
        )
        delivery_qty = _decimal_or_zero(item_in.delivery_quantity)
        if delivery_qty > remaining_qty:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"交付数量超出订单剩余数量：{order_item.material_code} "
                    f"剩余 {remaining_qty}"
                ),
            )

        requested_by_item[order_item.id] = already_requested + delivery_qty
        validated_items.append((item_in, order_item))

    return validated_items


def _receive_quantity_overrides(
    payload: Optional[dict[str, Any]],
) -> tuple[dict[int, Decimal], dict[int, Decimal]]:
    by_delivery_item: dict[int, Decimal] = {}
    by_order_item: dict[int, Decimal] = {}

    if not payload or not isinstance(payload, dict):
        return by_delivery_item, by_order_item

    for item in payload.get("items") or []:
        if not isinstance(item, dict):
            continue
        raw_quantity = item.get("received_quantity", item.get("quantity"))
        if raw_quantity is None:
            continue
        quantity = _decimal_or_zero(raw_quantity)
        if item.get("delivery_item_id") is not None:
            by_delivery_item[int(item["delivery_item_id"])] = quantity
        elif item.get("id") is not None:
            by_delivery_item[int(item["id"])] = quantity
        elif item.get("order_item_id") is not None:
            by_order_item[int(item["order_item_id"])] = quantity

    return by_delivery_item, by_order_item


# NOTE: keep flat routes (no extra prefix) to preserve the original API paths.
# 共 3 个路由

# ==================== 外协交付 ====================


@router.get(
    "/outsourcing-deliveries", response_model=PaginatedResponse, status_code=status.HTTP_200_OK
)
def read_outsourcing_deliveries(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    order_id: Optional[int] = Query(None, description="订单ID筛选"),
    vendor_id: Optional[int] = Query(None, description="外协商ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取交付记录列表
    """
    query = db.query(OutsourcingDelivery)

    if order_id:
        query = query.filter(OutsourcingDelivery.order_id == order_id)

    if vendor_id:
        query = query.filter(OutsourcingDelivery.vendor_id == vendor_id)

    if status:
        query = query.filter(OutsourcingDelivery.status == status)

    total = query.count()
    deliveries = apply_pagination(
        query.order_by(desc(OutsourcingDelivery.delivery_date)), pagination.offset, pagination.limit
    ).all()

    items = []
    for delivery in deliveries:
        vendor = (
            db.query(Vendor)
            .filter(Vendor.id == delivery.vendor_id, Vendor.vendor_type == "OUTSOURCING")
            .first()
        )
        order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()

        items.append(
            OutsourcingDeliveryResponse(
                id=delivery.id,
                delivery_no=delivery.delivery_no,
                order_id=delivery.order_id,
                order_no=order.order_no if order else None,
                vendor_name=vendor.supplier_name if vendor else None,
                delivery_date=delivery.delivery_date,
                delivery_type=delivery.delivery_type,
                status=delivery.status,
                received_at=delivery.received_at,
                created_at=delivery.created_at,
                updated_at=delivery.updated_at,
            )
        )

    return pagination.to_response(items, total)


@router.post(
    "/outsourcing-deliveries",
    response_model=OutsourcingDeliveryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_outsourcing_delivery(
    *,
    db: Session = Depends(deps.get_db),
    delivery_in: OutsourcingDeliveryCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建交付记录
    """
    # 验证订单
    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery_in.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="外协订单不存在")

    if order.status not in ["APPROVED", "IN_PROGRESS"]:
        raise HTTPException(status_code=400, detail="只能为已审批或进行中的订单创建交付记录")

    vendor = (
        db.query(Vendor)
        .filter(Vendor.id == order.vendor_id)
        .first()
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="外协商不存在")

    if not delivery_in.items:
        raise HTTPException(status_code=400, detail="交付明细不能为空")

    validated_items = _validate_delivery_items(db, delivery_in)

    delivery_no = generate_delivery_no(db)

    delivery = OutsourcingDelivery(
        delivery_no=delivery_no,
        order_id=delivery_in.order_id,
        vendor_id=order.vendor_id,
        delivery_date=delivery_in.delivery_date,
        delivery_type=delivery_in.delivery_type,
        delivery_person=delivery_in.delivery_person,
        logistics_company=delivery_in.logistics_company,
        tracking_no=delivery_in.tracking_no,
        status="PENDING",
        created_by=current_user.id,
        remark=delivery_in.remark,
    )

    db.add(delivery)
    db.flush()  # 获取delivery.id

    # 创建交付明细
    for item_in, order_item in validated_items:
        delivery_item = OutsourcingDeliveryItem(
            delivery_id=delivery.id,
            order_item_id=item_in.order_item_id,
            material_code=order_item.material_code,
            material_name=order_item.material_name,
            delivery_quantity=item_in.delivery_quantity,
            remark=item_in.remark,
        )
        db.add(delivery_item)

        # 更新订单明细的已交付数量
        order_item.delivered_quantity = (
            order_item.delivered_quantity or Decimal("0")
        ) + _decimal_or_zero(item_in.delivery_quantity)
        db.add(order_item)

    # 更新订单状态
    if order.status == "APPROVED":
        order.status = "IN_PROGRESS"
        db.add(order)

    db.commit()
    db.refresh(delivery)

    return _build_delivery_response(db, delivery)


@router.put(
    "/outsourcing-deliveries/{delivery_id}/receive",
    response_model=OutsourcingDeliveryResponse,
    status_code=status.HTTP_200_OK,
)
def receive_outsourcing_delivery(
    *,
    delivery_id: int,
    payload: Optional[dict[str, Any]] = Body(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """确认外协交付收货。"""
    delivery = db.query(OutsourcingDelivery).filter(OutsourcingDelivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="交付记录不存在")

    delivery_items = (
        db.query(OutsourcingDeliveryItem)
        .filter(OutsourcingDeliveryItem.delivery_id == delivery.id)
        .all()
    )
    if not delivery_items:
        raise HTTPException(status_code=400, detail="交付明细不能为空")

    quantity_by_delivery_item, quantity_by_order_item = _receive_quantity_overrides(payload)
    for delivery_item in delivery_items:
        received_quantity = quantity_by_delivery_item.get(
            delivery_item.id,
            quantity_by_order_item.get(
                delivery_item.order_item_id,
                _decimal_or_zero(delivery_item.delivery_quantity),
            ),
        )
        if received_quantity < Decimal("0"):
            raise HTTPException(status_code=400, detail="实收数量不能为负数")
        if received_quantity > _decimal_or_zero(delivery_item.delivery_quantity):
            raise HTTPException(status_code=400, detail="实收数量不能超过交付数量")
        delivery_item.received_quantity = received_quantity
        db.add(delivery_item)

    delivery.status = "RECEIVED"
    delivery.received_at = datetime.now()
    delivery.received_by = current_user.id
    db.add(delivery)

    order = db.query(OutsourcingOrder).filter(OutsourcingOrder.id == delivery.order_id).first()
    if order:
        _sync_order_receipt_status(db, order)

    db.commit()
    db.refresh(delivery)

    return _build_delivery_response(db, delivery)
