# -*- coding: utf-8 -*-
"""
采购订单端点
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.config import settings
from app.models.material import BomHeader
from app.models.vendor import Vendor
from app.models.purchase import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.data_scope_service import DataScopeConfig, DataScopeService

from .utils import (
    decimal_value,
    generate_order_no,
    serialize_order_item,
    serialize_purchase_order,
)

router = APIRouter()

# 采购订单数据权限配置
PO_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="created_by",
    additional_owner_fields=["approved_by"],
    project_field="project_id",
)


@router.get("/")
def list_purchase_orders(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购订单列表（按数据权限过滤）"""
    query = db.query(PurchaseOrder)

    # 应用数据权限过滤
    query = DataScopeService.filter_by_scope(
        db, query, PurchaseOrder, current_user, PO_DATA_SCOPE_CONFIG
    )

    if keyword:
        query = query.filter(
            or_(
                PurchaseOrder.order_no.like(f"%{keyword}%"),
                PurchaseOrder.order_title.like(f"%{keyword}%"),
            )
        )
    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    orders = (
        query.order_by(desc(PurchaseOrder.created_at)).offset(offset).limit(page_size).all()
    )
    return {
        "items": [serialize_purchase_order(o, include_items=False) for o in orders],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("/")
def create_purchase_order(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """创建采购订单"""
    supplier_id = payload.get("supplier_id")
    if not supplier_id:
        raise HTTPException(status_code=422, detail="supplier_id 必填")
    supplier = db.query(Vendor).filter(Vendor.id == supplier_id, Vendor.vendor_type == 'MATERIAL').first()
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    items_payload = payload.get("items") or []
    if not items_payload:
        raise HTTPException(status_code=400, detail="采购订单至少需要 1 条明细")

    order_no = generate_order_no(db, "PO")
    required_date = payload.get("required_date")
    parsed_required_date: Optional[date] = None
    if required_date:
        parsed_required_date = date.fromisoformat(required_date)

    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=supplier.id,
        project_id=payload.get("project_id"),
        order_type=payload.get("order_type") or "NORMAL",
        order_title=payload.get("order_title"),
        required_date=parsed_required_date,
        status="DRAFT",
        created_by=current_user.id,
        order_date=date.today(),
    )
    db.add(order)
    db.flush()

    total_amount = Decimal("0")
    for idx, item in enumerate(items_payload, start=1):
        qty = decimal_value(item.get("quantity"), "0")
        unit_price = decimal_value(item.get("unit_price"), "0")
        amount = qty * unit_price
        total_amount += amount

        order_item = PurchaseOrderItem(
            order_id=order.id,
            item_no=idx,
            material_id=item.get("material_id"),
            material_code=item.get("material_code") or "",
            material_name=item.get("material_name") or "",
            specification=item.get("specification"),
            unit=item.get("unit") or "件",
            quantity=qty,
            unit_price=unit_price,
            amount=amount,
            tax_rate=decimal_value(item.get("tax_rate"), "13"),
            required_date=parsed_required_date,
            status="PENDING",
        )
        db.add(order_item)

    order.total_amount = total_amount
    db.commit()
    db.refresh(order)
    return serialize_purchase_order(order, include_items=True)


@router.post("/from-bom")
def create_orders_from_bom(
    bom_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """从BOM生成采购订单（占位）"""
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")
    raise HTTPException(status_code=400, detail="未实现：请使用BOM拆单服务")


@router.get("/{order_id}")
def get_purchase_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购订单详情"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    return serialize_purchase_order(order, include_items=True)


@router.get("/{order_id}/items")
def get_purchase_order_items(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购订单明细"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    return [serialize_order_item(i) for i in order.items.order_by(PurchaseOrderItem.item_no).all()]


@router.put("/{order_id}")
def update_purchase_order(
    order_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新采购订单"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态可更新")

    for field in ("order_title", "required_date", "remark"):
        if field in payload:
            if field == "required_date" and payload[field]:
                setattr(order, field, date.fromisoformat(payload[field]))
            else:
                setattr(order, field, payload[field])
    db.commit()
    db.refresh(order)
    return serialize_purchase_order(order, include_items=True)


@router.put("/{order_id}/submit")
def submit_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """提交采购订单"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态可提交")
    if order.items.count() == 0:
        raise HTTPException(status_code=400, detail="采购订单没有明细")
    order.status = "SUBMITTED"
    order.submitted_at = datetime.now()
    db.commit()
    return ResponseModel(code=200, message="采购订单提交成功", data=None)


@router.put("/{order_id}/approve")
def approve_purchase_order(
    order_id: int,
    approved: bool = Query(True),
    approval_note: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """审批采购订单"""
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="采购订单不存在")
    if order.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交的订单可审批")

    order.approved_by = current_user.id
    order.approved_at = datetime.now()
    order.approval_note = approval_note
    order.status = "APPROVED" if approved else "REJECTED"
    db.commit()
    return ResponseModel(code=200, message="采购订单审批完成", data=None)
