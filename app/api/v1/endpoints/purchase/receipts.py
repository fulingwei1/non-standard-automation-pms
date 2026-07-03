# -*- coding: utf-8 -*-
"""
收货单端点
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404

from .utils import decimal_value, generate_receipt_no

router = APIRouter()


def _date_value(value: Any) -> Optional[str]:
    return value.isoformat() if value else None


def _empty_receipt(receipt_id: int) -> dict[str, Any]:
    return {
        "id": receipt_id,
        "receipt_no": f"GR-DEMO-{receipt_id:04d}",
        "order_id": None,
        "order_no": "",
        "supplier_id": None,
        "supplier_name": "",
        "receipt_date": date.today().isoformat(),
        "receipt_type": "NORMAL",
        "delivery_note_no": "",
        "logistics_company": "",
        "tracking_no": "",
        "status": "PENDING",
        "inspect_status": "PENDING",
        "inspected_at": None,
        "warehoused_at": None,
        "remark": "",
        "items": [],
        "not_found": True,
    }


def _serialize_receipt_item(item: GoodsReceiptItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "receipt_id": item.receipt_id,
        "order_item_id": item.order_item_id,
        "material_code": item.material_code,
        "material_name": item.material_name,
        "delivery_qty": float(item.delivery_qty or 0),
        "received_qty": float(item.received_qty or 0),
        "inspect_qty": float(item.inspect_qty or 0),
        "qualified_qty": float(item.qualified_qty or 0),
        "rejected_qty": float(item.rejected_qty or 0),
        "inspect_result": item.inspect_result,
        "inspect_note": item.inspect_note,
        "warehoused_qty": float(item.warehoused_qty or 0),
        "warehouse_location": item.warehouse_location,
        "amount": float(item.amount or 0),
        "remark": item.remark,
    }


def _serialize_receipt(receipt: GoodsReceipt, include_items: bool = False) -> dict[str, Any]:
    order = receipt.order
    vendor = getattr(order, "vendor", None) if order else None
    data = {
        "id": receipt.id,
        "receipt_no": receipt.receipt_no,
        "order_id": receipt.order_id,
        "order_no": getattr(order, "order_no", "") or "",
        "supplier_id": receipt.supplier_id,
        "supplier_name": getattr(vendor, "supplier_name", "") or "",
        "receipt_date": _date_value(receipt.receipt_date),
        "receipt_type": receipt.receipt_type,
        "delivery_note_no": receipt.delivery_note_no,
        "logistics_company": receipt.logistics_company,
        "tracking_no": receipt.tracking_no,
        "status": receipt.status,
        "inspect_status": receipt.inspect_status,
        "inspected_at": _date_value(receipt.inspected_at),
        "warehoused_at": _date_value(receipt.warehoused_at),
        "remark": receipt.remark,
    }
    if include_items:
        data["items"] = [_serialize_receipt_item(item) for item in receipt.items.all()]
    return data


@router.get("/goods-receipts/")
def list_goods_receipts(
    order_id: Optional[int] = Query(None, description="采购订单ID"),
    status: Optional[str] = Query(None, description="收货状态"),
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(get_current_active_user),
):
    """获取收货单列表"""
    query = db.query(GoodsReceipt)
    if order_id is not None:
        query = query.filter(GoodsReceipt.order_id == order_id)
    if status:
        query = query.filter(GoodsReceipt.status == status)
    total = query.count()
    receipts = apply_pagination(
        query.order_by(desc(GoodsReceipt.created_at)), pagination.offset, pagination.limit
    ).all()
    return {
        "items": [
            {
                "id": receipt.id,
                "receipt_no": receipt.receipt_no,
                "order_id": receipt.order_id,
                "supplier_id": receipt.supplier_id,
                "receipt_date": receipt.receipt_date.isoformat(),
                "status": receipt.status,
            }
            for receipt in receipts
        ],
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": (total + pagination.page_size - 1) // pagination.page_size,
    }


@router.get("/goods-receipts/{receipt_id}")
def get_goods_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取收货单详情。"""
    receipt = db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
    if not receipt:
        return _empty_receipt(receipt_id)
    return _serialize_receipt(receipt, include_items=True)


@router.get("/goods-receipts/{receipt_id}/items")
def list_goods_receipt_items(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> List[dict[str, Any]]:
    """获取收货单明细。"""
    receipt = db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
    if not receipt:
        return []
    return [_serialize_receipt_item(item) for item in receipt.items.all()]


@router.post("/goods-receipts/")
def create_goods_receipt(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建收货单"""
    order_id = payload.get("order_id")
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")

    # NP1: 仅已审批(或收货中)的采购订单可收货；草稿/待审/已驳回/已取消不可收货
    _ost = str(order.status or "").upper()
    if _ost not in ("APPROVED", "PARTIAL_RECEIVED", "PARTIALLY_RECEIVED", "RECEIVING", "RECEIVED"):
        raise HTTPException(status_code=400, detail=f"采购订单状态为 {order.status}，只有已审批的订单可以收货")

    receipt_date = date.fromisoformat(payload.get("receipt_date") or date.today().isoformat())
    items_payload = payload.get("items") or []
    if not items_payload:
        raise HTTPException(status_code=400, detail="收货单至少需要 1 条明细")

    validated_items = []
    received_by_order_item: dict[int, Decimal] = {}
    for item in items_payload:
        order_item_id = item.get("order_item_id")
        order_item = get_or_404(db, PurchaseOrderItem, order_item_id, "订单明细不存在")
        if order_item.order_id != order.id:
            raise HTTPException(status_code=400, detail="订单明细不属于该采购订单")

        delivery_qty = decimal_value(item.get("delivery_qty"), "0")
        received_qty = decimal_value(item.get("received_qty"), "0")
        if received_qty > delivery_qty:
            raise HTTPException(status_code=400, detail="实收数量不能大于送货数量")

        already_received = order_item.received_qty or Decimal("0")
        payload_received = received_by_order_item.get(order_item.id, Decimal("0"))
        remaining_qty = (order_item.quantity or Decimal("0")) - already_received - payload_received
        if delivery_qty > remaining_qty or received_qty > remaining_qty:
            raise HTTPException(
                status_code=400,
                detail=f"收货数量超过订单剩余数量，剩余可收 {remaining_qty}",
            )

        received_by_order_item[order_item.id] = payload_received + received_qty
        validated_items.append((order_item, delivery_qty, received_qty))

    receipt = GoodsReceipt(
        receipt_no=generate_receipt_no(db),
        order_id=order.id,
        supplier_id=order.supplier_id,
        receipt_date=receipt_date,
        receipt_type=payload.get("receipt_type") or "NORMAL",
        delivery_note_no=payload.get("delivery_note_no"),
        status="PENDING",
        created_by=current_user.id,
    )
    db.add(receipt)
    db.flush()

    for order_item, delivery_qty, received_qty in validated_items:
        receipt_item = GoodsReceiptItem(
            receipt_id=receipt.id,
            order_item_id=order_item.id,
            material_code=order_item.material_code,
            material_name=order_item.material_name,
            delivery_qty=delivery_qty,
            received_qty=received_qty,
        )
        db.add(receipt_item)

        order_item.received_qty = (order_item.received_qty or Decimal("0")) + received_qty

    db.commit()
    return ResponseModel(code=200, message="收货单创建成功", data={"id": receipt.id})


@router.put("/goods-receipts/{receipt_id}/receive")
def update_goods_receipt_status(
    receipt_id: int,
    status: str = Query("RECEIVED", description="收货状态"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新收货单状态。"""
    receipt = db.query(GoodsReceipt).filter(GoodsReceipt.id == receipt_id).first()
    if not receipt:
        return ResponseModel(
            code=200,
            message="收货单不存在，已按空态处理",
            data=_empty_receipt(receipt_id),
        )

    receipt.status = status
    if status == "RECEIVED":
        receipt.warehoused_at = datetime.now()
        receipt.warehoused_by = current_user.id
    db.commit()
    db.refresh(receipt)
    return ResponseModel(code=200, message="收货状态已更新", data=_serialize_receipt(receipt))


@router.put("/goods-receipts/{receipt_id}/items/{item_id}/inspect")
def inspect_receipt_item(
    receipt_id: int,
    item_id: int,
    inspect_qty: float = Query(..., gt=0),
    qualified_qty: float = Query(..., ge=0),
    rejected_qty: Optional[float] = Query(None, ge=0),
    inspect_result: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """质检收货明细"""
    receipt_item = (
        db.query(GoodsReceiptItem)
        .filter(GoodsReceiptItem.receipt_id == receipt_id, GoodsReceiptItem.id == item_id)
        .first()
    )
    if not receipt_item:
        raise HTTPException(status_code=404, detail="收货明细不存在")

    inspect_qty_value = decimal_value(inspect_qty, "0")
    qualified_qty_value = decimal_value(qualified_qty, "0")
    rejected_qty_value = (
        decimal_value(rejected_qty, "0")
        if rejected_qty is not None
        else inspect_qty_value - qualified_qty_value
    )

    if qualified_qty_value > inspect_qty_value:
        raise HTTPException(status_code=400, detail="合格数量不能大于送检数量")

    if rejected_qty_value < Decimal("0"):
        raise HTTPException(status_code=400, detail="不合格数量不能小于0")

    if qualified_qty_value + rejected_qty_value != inspect_qty_value:
        raise HTTPException(status_code=400, detail="合格数量 + 不合格数量必须等于送检数量")

    if inspect_qty_value > (receipt_item.received_qty or Decimal("0")):
        raise HTTPException(status_code=400, detail="送检数量不能大于实收数量")

    computed_result = "PARTIAL"
    if rejected_qty_value == Decimal("0"):
        computed_result = "QUALIFIED"
    elif qualified_qty_value == Decimal("0"):
        computed_result = "UNQUALIFIED"

    if inspect_result:
        requested_result = inspect_result.upper()
        valid_results = {"QUALIFIED", "UNQUALIFIED", "PARTIAL"}
        if requested_result not in valid_results:
            raise HTTPException(status_code=400, detail="质检结果不合法")
        if requested_result != computed_result:
            raise HTTPException(status_code=400, detail="质检结果与数量不一致")

    receipt_item.inspect_qty = inspect_qty_value
    receipt_item.qualified_qty = qualified_qty_value
    receipt_item.rejected_qty = rejected_qty_value
    receipt_item.inspect_result = computed_result
    receipt_item.receipt.inspect_status = computed_result
    receipt_item.receipt.inspected_at = datetime.now()
    receipt_item.receipt.inspected_by = current_user.id
    db.commit()
    return ResponseModel(code=200, message="质检结果已更新", data=None)
