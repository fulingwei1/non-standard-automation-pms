# -*- coding: utf-8 -*-
"""
采购订单端点（重构版）
使用统一响应格式
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.schemas import list_response, paginated_response, success_response
from app.models.vendor import Vendor
from app.models.purchase import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.user import User
from app.services.data_scope_service import DataScopeConfig, DataScopeService
from app.common.pagination import PaginationParams, get_pagination_query

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
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购订单列表（按数据权限过滤）"""
    try:
        query = db.query(PurchaseOrder)

        # 应用数据权限过滤
        query = DataScopeService.filter_by_scope(
            db, query, PurchaseOrder, current_user, PO_DATA_SCOPE_CONFIG
        )

        # 应用关键词过滤（订单号/标题）
        from app.common.query_filters import apply_keyword_filter
        query = apply_keyword_filter(query, PurchaseOrder, keyword, ["order_no", "order_title"])

        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        if status:
            query = query.filter(PurchaseOrder.status == status)

        # 日期范围过滤（基于 order_date 字段，如果为 None 则跳过该订单）
        if start_date:
            try:
                start_date_obj = date.fromisoformat(start_date)
                query = query.filter(
                    and_(
                        PurchaseOrder.order_date.isnot(None),
                        PurchaseOrder.order_date >= start_date_obj
                    )
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="start_date 格式错误，应为 YYYY-MM-DD")
        if end_date:
            try:
                end_date_obj = date.fromisoformat(end_date)
                query = query.filter(
                    and_(
                        PurchaseOrder.order_date.isnot(None),
                        PurchaseOrder.order_date <= end_date_obj
                    )
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="end_date 格式错误，应为 YYYY-MM-DD")

        total = query.count()
        orders = (
            apply_pagination(query.order_by(desc(PurchaseOrder.created_at)), pagination.offset, pagination.limit).all()
        )

        items = [serialize_purchase_order(o, include_items=False) for o in orders]

        # 使用统一响应格式
        return paginated_response(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
    except HTTPException:
        # 重新抛出 HTTP 异常（如参数验证错误）
        raise
    except Exception as e:
        # 记录详细错误信息
        logging.error(f"获取采购订单列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="获取采购订单失败，请稍后重试"
        )


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
    
    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_order(order, include_items=True),
        message="采购订单创建成功"
    )


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
    
    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_order(order, include_items=True),
        message="获取采购订单详情成功"
    )


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
    
    try:
        items = [serialize_order_item(i) for i in order.items.order_by(PurchaseOrderItem.item_no).all()]
    except Exception:
        items = []
    
    # 使用统一响应格式
    return list_response(
        items=items,
        message="获取采购订单明细成功"
    )


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
    
    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_order(order, include_items=True),
        message="采购订单更新成功"
    )


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
    try:
        items_count = order.items.count()
    except Exception:
        items_count = 0
    if items_count == 0:
        raise HTTPException(status_code=400, detail="采购订单没有明细")
    order.status = "SUBMITTED"
    order.submitted_at = datetime.now()
    db.commit()
    
    # 使用统一响应格式
    return success_response(
        data=None,
        message="采购订单提交成功"
    )


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
    
    # 使用统一响应格式
    return success_response(
        data=None,
        message="采购订单审批完成"
    )
