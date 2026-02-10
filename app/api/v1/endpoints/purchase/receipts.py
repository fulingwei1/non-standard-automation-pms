# -*- coding: utf-8 -*-
"""
收货单端点
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.purchase import (
    GoodsReceipt,
    GoodsReceiptItem,
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.common.pagination import PaginationParams, get_pagination_query

from .utils import decimal_value, generate_receipt_no

router = APIRouter()


@router.get("/goods-receipts/")
def list_goods_receipts(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(get_current_active_user),
):
    """获取收货单列表"""
    query = db.query(GoodsReceipt)
    total = query.count()
    receipts = query.order_by(desc(GoodsReceipt.created_at)).offset(pagination.offset).limit(pagination.limit).all()
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
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/goods-receipts/")
def create_goods_receipt(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建收货单"""
    order_id = payload.get("order_id")
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")

    receipt_date = date.fromisoformat(payload.get("receipt_date") or date.today().isoformat())
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

    items_payload = payload.get("items") or []
    if not items_payload:
        raise HTTPException(status_code=400, detail="收货单至少需要 1 条明细")

    for item in items_payload:
        order_item_id = item.get("order_item_id")
        order_item = db.query(PurchaseOrderItem).filter(PurchaseOrderItem.id == order_item_id).first()
        if not order_item:
            raise HTTPException(status_code=404, detail="订单明细不存在")

        delivery_qty = decimal_value(item.get("delivery_qty"), "0")
        received_qty = decimal_value(item.get("received_qty"), "0")
        if received_qty > delivery_qty:
            raise HTTPException(status_code=400, detail="实收数量不能大于送货数量")

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


@router.put("/goods-receipts/{receipt_id}/items/{item_id}/inspect")
def inspect_receipt_item(
    receipt_id: int,
    item_id: int,
    inspect_qty: float = Query(..., gt=0),
    qualified_qty: float = Query(..., ge=0),
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

    if qualified_qty > inspect_qty:
        raise HTTPException(status_code=400, detail="合格数量不能大于送检数量")

    if Decimal(str(inspect_qty)) > (receipt_item.received_qty or Decimal("0")):
        raise HTTPException(status_code=400, detail="送检数量不能大于实收数量")

    receipt_item.inspect_qty = decimal_value(inspect_qty, "0")
    receipt_item.qualified_qty = decimal_value(qualified_qty, "0")
    receipt_item.rejected_qty = decimal_value(inspect_qty - qualified_qty, "0")
    receipt_item.inspect_result = "PASS" if qualified_qty == inspect_qty else "FAIL"
    receipt_item.receipt.inspect_status = "COMPLETED"
    receipt_item.receipt.inspected_at = datetime.now()
    receipt_item.receipt.inspected_by = current_user.id
    db.commit()
    return ResponseModel(code=200, message="质检结果已更新", data=None)
