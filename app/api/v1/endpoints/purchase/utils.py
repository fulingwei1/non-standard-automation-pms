# -*- coding: utf-8 -*-
"""
采购管理辅助函数和序列化
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.purchase import (
    GoodsReceipt,
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
)


def decimal_value(value: Any, default: str = "0") -> Decimal:
    """安全转换为 Decimal"""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def generate_order_no(db: Session, prefix: str = "PO") -> str:
    """生成采购订单编号"""
    today = datetime.now().strftime("%Y%m%d")
    like_pattern = f"{prefix}-{today}-%"
    max_no = (
        db.query(PurchaseOrder.order_no)
        .filter(PurchaseOrder.order_no.like(like_pattern))
        .order_by(desc(PurchaseOrder.order_no))
        .first()
    )
    if max_no and max_no[0]:
        try:
            seq = int(max_no[0].split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"{prefix}-{today}-{seq:03d}"


def generate_request_no(db: Session) -> str:
    """生成采购申请编号"""
    today = datetime.now().strftime("%Y%m%d")
    like_pattern = f"PR-{today}-%"
    max_no = (
        db.query(PurchaseRequest.request_no)
        .filter(PurchaseRequest.request_no.like(like_pattern))
        .order_by(desc(PurchaseRequest.request_no))
        .first()
    )
    if max_no and max_no[0]:
        try:
            seq = int(max_no[0].split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"PR-{today}-{seq:03d}"


def generate_receipt_no(db: Session) -> str:
    """生成收货单编号"""
    today = datetime.now().strftime("%Y%m%d")
    like_pattern = f"GR-{today}-%"
    max_no = (
        db.query(GoodsReceipt.receipt_no)
        .filter(GoodsReceipt.receipt_no.like(like_pattern))
        .order_by(desc(GoodsReceipt.receipt_no))
        .first()
    )
    if max_no and max_no[0]:
        try:
            seq = int(max_no[0].split("-")[-1]) + 1
        except Exception:
            seq = 1
    else:
        seq = 1
    return f"GR-{today}-{seq:03d}"


def serialize_order_item(item: PurchaseOrderItem) -> Dict[str, Any]:
    """序列化采购订单明细"""
    return {
        "id": item.id,
        "item_no": item.item_no,
        "material_id": item.material_id,
        "material_code": item.material_code,
        "material_name": item.material_name,
        "specification": item.specification,
        "unit": item.unit,
        "quantity": float(item.quantity or 0),
        "unit_price": float(item.unit_price or 0),
        "amount": float(item.amount or 0),
        "tax_rate": float(item.tax_rate or 0),
        "required_date": item.required_date.isoformat() if item.required_date else None,
        "status": item.status,
    }


def serialize_purchase_order(order: PurchaseOrder, *, include_items: bool = False) -> Dict[str, Any]:
    """序列化采购订单"""
    data: Dict[str, Any] = {
        "id": order.id,
        "order_no": order.order_no,
        "supplier_id": order.supplier_id,
        "project_id": order.project_id,
        "order_type": order.order_type,
        "order_title": order.order_title,
        "total_amount": float(order.total_amount or 0),
        "status": order.status,
        "required_date": order.required_date.isoformat() if order.required_date else None,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }
    if include_items:
        data["items"] = [serialize_order_item(i) for i in order.items.order_by(PurchaseOrderItem.item_no).all()]
    return data


def serialize_purchase_request(request: PurchaseRequest, *, include_items: bool = False) -> Dict[str, Any]:
    """序列化采购申请"""
    data: Dict[str, Any] = {
        "id": request.id,
        "request_no": request.request_no,
        "project_id": request.project_id,
        "machine_id": request.machine_id,
        "supplier_id": request.supplier_id,
        "request_type": request.request_type,
        "request_reason": request.request_reason,
        "required_date": request.required_date.isoformat() if request.required_date else None,
        "total_amount": float(request.total_amount or 0),
        "status": request.status,
        "created_at": request.created_at.isoformat() if request.created_at else None,
    }
    if include_items:
        data["items"] = [
            {
                "id": item.id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "unit": item.unit,
                "quantity": float(item.quantity or 0),
                "unit_price": float(item.unit_price or 0),
                "amount": float(item.amount or 0),
                "required_date": item.required_date.isoformat() if item.required_date else None,
            }
            for item in request.items.order_by(PurchaseRequestItem.id).all()
        ]
    return data
