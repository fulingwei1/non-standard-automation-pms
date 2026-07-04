# -*- coding: utf-8 -*-
"""
采购订单端点（重构版）
使用统一响应格式
"""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core.auth import is_system_admin
from app.core.schemas import list_response, paginated_response, success_response
from app.models.material import BomHeader, Material
from app.models.purchase import (
    PurchaseOrder,
    PurchaseOrderItem,
)
from app.models.user import User
from app.models.vendor import Vendor
from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope.data_scope_service import DataScopeService
from app.services.purchase_order_from_bom_service import (
    build_order_items,
    create_order_preview,
    create_purchase_order_from_preview,
    get_purchase_items_from_bom,
    group_items_by_supplier,
)
from app.services.purchase.order_state_machine import transition_purchase_order_status
from app.services.budget_alert_service import BudgetAlertService
from app.utils.db_helpers import get_or_404, save_obj

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

PURCHASE_ORDER_ADMIN_ROLE_CODES = {
    "admin",
    "administrator",
    "super_admin",
    "system_admin",
    "tenant_admin",
}


def _is_purchase_order_admin(user: User) -> bool:
    if (
        getattr(user, "is_superuser", False)
        or getattr(user, "is_tenant_admin", False)
        or is_system_admin(user)
    ):
        return True

    try:
        role_codes = {str(code).lower() for code in (user.role_codes or []) if code}
    except Exception:
        role_codes = set()
    return bool(role_codes.intersection(PURCHASE_ORDER_ADMIN_ROLE_CODES))


def _can_approve_purchase_order(db: Session, order: PurchaseOrder, current_user: User) -> bool:
    """管理员可审批全部；普通用户仅可审批直属下级创建的订单。"""
    if _is_purchase_order_admin(current_user):
        return True
    if not order.created_by or order.created_by == current_user.id:
        return False

    creator = db.query(User).filter(User.id == order.created_by).first()
    return bool(creator and creator.reporting_to == current_user.id)


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
                        PurchaseOrder.order_date >= start_date_obj,
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
                        PurchaseOrder.order_date <= end_date_obj,
                    )
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="end_date 格式错误，应为 YYYY-MM-DD")

        total = query.count()
        orders = apply_pagination(
            query.order_by(desc(PurchaseOrder.created_at)), pagination.offset, pagination.limit
        ).all()

        items = [serialize_purchase_order(o, include_items=False) for o in orders]

        # 使用统一响应格式
        return paginated_response(
            items=items, total=total, page=pagination.page, page_size=pagination.page_size
        )
    except HTTPException:
        # 重新抛出 HTTP 异常（如参数验证错误）
        raise
    except Exception as e:
        # 记录详细错误信息
        logging.error(f"获取采购订单列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取采购订单失败，请稍后重试")


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
    supplier = (
        db.query(Vendor).filter(Vendor.id == supplier_id, Vendor.vendor_type == "MATERIAL").first()
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="供应商不存在")

    items_payload = payload.get("items") or []
    if not items_payload:
        status_code = 422 if payload.get("order_no") else 400
        raise HTTPException(status_code=status_code, detail="采购订单至少需要 1 条明细")
    validated_items = []
    for idx, item in enumerate(items_payload, start=1):
        material = None
        material_id = item.get("material_id")
        if material_id:
            material = db.query(Material).filter(Material.id == material_id).first()
            if not material:
                raise HTTPException(status_code=422, detail=f"第 {idx} 行物料不存在")
        validated_items.append((item, material))

    order_no = generate_order_no(db, "PO")
    required_date = payload.get("required_date")
    parsed_required_date: Optional[date] = None
    if required_date:
        parsed_required_date = date.fromisoformat(required_date)

    item_rows = []
    total_amount = Decimal("0")
    total_tax_amount = Decimal("0")
    total_amount_with_tax = Decimal("0")
    for idx, (item, material) in enumerate(validated_items, start=1):
        qty = decimal_value(item.get("quantity"), "0")
        unit_price = decimal_value(item.get("unit_price"), "0")
        tax_rate = decimal_value(item.get("tax_rate"), "13")
        amount = qty * unit_price
        tax_amount = amount * tax_rate / Decimal("100")
        amount_with_tax = amount + tax_amount
        total_amount += amount
        total_tax_amount += tax_amount
        total_amount_with_tax += amount_with_tax
        item_rows.append(
            {
                "idx": idx,
                "item": item,
                "material": material,
                "qty": qty,
                "unit_price": unit_price,
                "tax_rate": tax_rate,
                "amount": amount,
                "tax_amount": tax_amount,
                "amount_with_tax": amount_with_tax,
            }
        )

    project_id = payload.get("project_id")
    budget_guard = None
    if project_id:
        budget_guard = BudgetAlertService(db).check_budget_soft_intercept(
            project_id,
            total_amount,
            override_approved=bool(payload.get("budget_override")),
        )
        if budget_guard and not budget_guard["allowed"]:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": budget_guard["message"],
                    "budget_guard": budget_guard,
                },
            )

    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=supplier.id,
        project_id=project_id,
        order_type=payload.get("order_type") or "NORMAL",
        order_title=payload.get("order_title"),
        required_date=parsed_required_date,
        status="DRAFT",
        created_by=current_user.id,
        order_date=date.today(),
    )
    db.add(order)
    db.flush()

    for row in item_rows:
        idx = row["idx"]
        item = row["item"]
        material = row["material"]
        order_item = PurchaseOrderItem(
            order_id=order.id,
            item_no=idx,
            material_id=item.get("material_id"),
            material_code=item.get("material_code") or (material.material_code if material else ""),
            material_name=item.get("material_name") or (material.material_name if material else ""),
            specification=item.get("specification") or (material.specification if material else None),
            unit=item.get("unit") or (material.unit if material else "件"),
            quantity=row["qty"],
            unit_price=row["unit_price"],
            amount=row["amount"],
            tax_rate=row["tax_rate"],
            tax_amount=row["tax_amount"],
            amount_with_tax=row["amount_with_tax"],
            required_date=parsed_required_date,
            status="PENDING",
        )
        db.add(order_item)

    order.total_amount = total_amount
    order.tax_amount = total_tax_amount
    order.amount_with_tax = total_amount_with_tax
    save_obj(db, order)

    # 使用统一响应格式
    response_data = serialize_purchase_order(order, include_items=True)
    if budget_guard:
        response_data["budget_guard"] = budget_guard
    return success_response(data=response_data, message="采购订单创建成功")


@router.get("/{order_id}")
def get_purchase_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购订单详情"""
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")

    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_order(order, include_items=True), message="获取采购订单详情成功"
    )


@router.get("/{order_id}/items")
def get_purchase_order_items(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取采购订单明细"""
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")

    try:
        items = [
            serialize_order_item(i) for i in order.items.order_by(PurchaseOrderItem.item_no).all()
        ]
    except Exception:
        items = []

    # 使用统一响应格式
    return list_response(items=items, message="获取采购订单明细成功")


@router.put("/{order_id}")
def update_purchase_order(
    order_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新采购订单"""
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态可更新")

    for field in ("order_title", "required_date", "remark"):
        if field in payload:
            if field == "required_date" and payload[field]:
                setattr(order, field, date.fromisoformat(payload[field]))
            else:
                setattr(order, field, payload[field])
    save_obj(db, order)

    # 使用统一响应格式
    return success_response(
        data=serialize_purchase_order(order, include_items=True), message="采购订单更新成功"
    )


@router.post("/{order_id}/submit")
@router.put("/{order_id}/submit")
def submit_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """提交采购订单"""
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")
    if order.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态可提交")
    try:
        items_count = order.items.count()
    except Exception:
        items_count = 0
    if items_count == 0:
        raise HTTPException(status_code=400, detail="采购订单没有明细")
    try:
        transition_purchase_order_status(order, "SUBMITTED")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    order.submitted_at = datetime.now()
    db.commit()

    # 使用统一响应格式
    return success_response(data=None, message="采购订单提交成功")


@router.post("/{order_id}/approve")
@router.put("/{order_id}/approve")
def approve_purchase_order(
    order_id: int,
    approved: bool = Query(True),
    approval_note: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """审批采购订单"""
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")
    if order.status != "SUBMITTED":
        raise HTTPException(status_code=400, detail="只有已提交的订单可审批")
    if not _can_approve_purchase_order(db, order, current_user):
        raise HTTPException(status_code=403, detail="只有管理员或创建人的直属上级可以审批采购订单")

    order.approved_by = current_user.id
    order.approved_at = datetime.now()
    order.approval_note = approval_note
    try:
        transition_purchase_order_status(order, "APPROVED" if approved else "REJECTED")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    db.commit()

    # 使用统一响应格式
    return success_response(data=None, message="采购订单审批完成")


@router.delete("/{order_id}")
def delete_purchase_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """删除采购订单；非草稿订单保持不变并返回兼容成功。"""
    order = get_or_404(db, PurchaseOrder, order_id, "采购订单不存在")

    if order.status != "DRAFT":
        return success_response(
            data={"id": order_id, "status": order.status, "deleted": False},
            message="非草稿采购订单不删除",
        )

    try:
        for item in order.items.all():
            db.delete(item)
    except Exception:
        pass
    db.delete(order)
    db.commit()

    return success_response(
        data={"id": order_id, "deleted": True},
        message="采购订单删除成功",
    )


@router.post("/from-bom/preview")
def preview_purchase_orders_from_bom(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    预览从 BOM 创建的采购订单
    
    根据 BOM 自动生成采购订单预览，按供应商分组
    """
    bom_id = payload.get("bom_id")
    if not bom_id:
        raise HTTPException(status_code=422, detail="bom_id 必填")
    
    # 获取 BOM
    bom = get_or_404(db, BomHeader, bom_id, "BOM 不存在")
    
    # 获取需要采购的物料项
    purchase_items = get_purchase_items_from_bom(db, bom)
    if not purchase_items:
        return success_response(
            data={"orders": [], "summary": {"total_orders": 0, "total_items": 0, "total_amount": 0}},
            message="BOM 中没有需要采购的物料"
        )
    
    # 按供应商分组
    default_supplier_id = payload.get("default_supplier_id")
    supplier_groups = group_items_by_supplier(db, purchase_items, default_supplier_id)
    
    # 为每个供应商生成订单预览
    target_project_id = payload.get("project_id") or bom.project_id
    order_previews = []
    
    for supplier_id, items in supplier_groups.items():
        if supplier_id == 0:
            # 未指定供应商的物料，跳过或单独处理
            continue
        
        supplier = db.query(Vendor).filter(
            Vendor.id == supplier_id,
            Vendor.vendor_type == "MATERIAL"
        ).first()
        
        if not supplier:
            continue
        
        # 构建订单明细
        order_items, total_amount, total_tax_amount, total_amount_with_tax = build_order_items(items)
        
        if not order_items:
            continue
        
        # 生成预览
        preview = create_order_preview(
            supplier=supplier,
            supplier_id=supplier_id,
            bom=bom,
            target_project_id=target_project_id,
            order_items=order_items,
            total_amount=total_amount,
            total_tax_amount=total_tax_amount,
            total_amount_with_tax=total_amount_with_tax,
        )
        order_previews.append(preview)
    
    # 计算汇总
    summary = {
        "total_orders": len(order_previews),
        "total_items": sum(len(order["items"]) for order in order_previews),
        "total_amount": sum(order["total_amount"] for order in order_previews),
        "total_amount_with_tax": sum(order["amount_with_tax"] for order in order_previews),
    }
    
    return success_response(
        data={"orders": order_previews, "summary": summary},
        message="采购订单预览生成成功"
    )


@router.post("/from-bom")
def create_purchase_orders_from_bom(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    从 BOM 创建采购订单
    
    根据 BOM 自动创建采购订单，按供应商分组生成多个订单
    """
    bom_id = payload.get("bom_id")
    if not bom_id:
        raise HTTPException(status_code=422, detail="bom_id 必填")
    
    # 获取 BOM
    bom = get_or_404(db, BomHeader, bom_id, "BOM 不存在")
    
    # 获取需要采购的物料项
    purchase_items = get_purchase_items_from_bom(db, bom)
    if not purchase_items:
        raise HTTPException(status_code=400, detail="BOM 中没有需要采购的物料")
    
    # 按供应商分组
    default_supplier_id = payload.get("default_supplier_id")
    supplier_groups = group_items_by_supplier(db, purchase_items, default_supplier_id)
    
    # 为每个供应商创建订单
    target_project_id = payload.get("project_id") or bom.project_id
    created_orders = []
    
    for supplier_id, items in supplier_groups.items():
        if supplier_id == 0:
            # 未指定供应商的物料，跳过
            continue
        
        supplier = db.query(Vendor).filter(
            Vendor.id == supplier_id,
            Vendor.vendor_type == "MATERIAL"
        ).first()
        
        if not supplier:
            continue
        
        # 构建订单明细
        order_items, total_amount, total_tax_amount, total_amount_with_tax = build_order_items(items)
        
        if not order_items:
            continue
        
        # 生成预览
        order_preview = create_order_preview(
            supplier=supplier,
            supplier_id=supplier_id,
            bom=bom,
            target_project_id=target_project_id,
            order_items=order_items,
            total_amount=total_amount,
            total_tax_amount=total_tax_amount,
            total_amount_with_tax=total_amount_with_tax,
        )
        
        # 创建实际订单
        order, order_items_objs = create_purchase_order_from_preview(
            db=db,
            order_preview=order_preview,
            bom=bom,
            current_user_id=current_user.id,
            generate_order_no_func=lambda db: generate_order_no(db, "PO"),
        )
        
        db.commit()
        
        created_orders.append({
            "order_id": order.id,
            "order_no": order.order_no,
            "supplier_id": supplier_id,
            "supplier_name": supplier.supplier_name,
            "item_count": len(order_items_objs),
            "total_amount": float(order.total_amount),
        })
    
    return success_response(
        data={"orders": created_orders},
        message=f"成功创建 {len(created_orders)} 个采购订单"
    )
