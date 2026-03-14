# -*- coding: utf-8 -*-
"""
从BOM创建采购订单服务
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem, Material
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem
from app.models.vendor import Vendor

INACTIVE_REQUEST_STATUSES = {"CANCELLED", "REJECTED"}
INACTIVE_ORDER_STATUSES = {"CANCELLED", "REJECTED"}


def get_purchase_items_from_bom(db: Session, bom: BomHeader) -> List[BomItem]:
    """
    获取BOM中需要采购的物料

    Returns:
        List[BomItem]: 需要采购的BOM物料项列表
    """
    return bom.items.filter(BomItem.source_type == "PURCHASE").all()


def determine_supplier_for_item(
    db: Session, item: BomItem, default_supplier_id: Optional[int]
) -> Optional[int]:
    """
    确定物料的供应商

    Returns:
        Optional[int]: 供应商ID，如果无法确定则返回None
    """
    if default_supplier_id:
        return default_supplier_id

    if item.supplier_id:
        return item.supplier_id

    if item.material_id:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        if material and material.default_supplier_id:
            return material.default_supplier_id

    return None


def group_items_by_supplier(
    db: Session, bom_items: List[BomItem], default_supplier_id: Optional[int]
) -> Dict[int, List[BomItem]]:
    """
    按供应商分组物料

    Returns:
        Dict[int, List[BomItem]]: 供应商ID到物料列表的映射
    """
    supplier_items = defaultdict(list)

    for item in bom_items:
        supplier_id = determine_supplier_for_item(db, item, default_supplier_id)
        supplier_items[supplier_id or 0].append(item)

    return dict(supplier_items)


def calculate_order_item(item: BomItem, item_no: int, remaining_qty: Decimal) -> Dict[str, Any]:
    """
    计算订单明细项

    Returns:
        Dict[str, Any]: 订单明细项数据
    """
    unit_price = item.unit_price or Decimal(0)
    tax_rate = Decimal(13)
    amount = remaining_qty * unit_price
    tax_amount = amount * tax_rate / 100
    amount_with_tax = amount + tax_amount

    return {
        "item_no": item_no,
        "material_id": item.material_id,
        "bom_item_id": item.id,
        "material_code": item.material_code,
        "material_name": item.material_name,
        "specification": item.specification,
        "unit": item.unit or "件",
        "quantity": remaining_qty,
        "unit_price": unit_price,
        "tax_rate": tax_rate,
        "amount": amount,
        "tax_amount": tax_amount,
        "amount_with_tax": amount_with_tax,
        "required_date": item.required_date,
    }


def build_order_items(
    items: List[BomItem],
    remaining_qty_by_bom_item: Optional[Dict[int, Decimal]] = None,
) -> Tuple[List[Dict[str, Any]], Decimal, Decimal, Decimal]:
    """
    构建订单明细列表

    Returns:
        Tuple[List[Dict[str, Any]], Decimal, Decimal, Decimal]:
        (订单明细列表, 总金额, 总税额, 含税总金额)
    """
    order_items = []
    total_amount = Decimal(0)
    total_tax_amount = Decimal(0)
    total_amount_with_tax = Decimal(0)
    remaining_qty_by_bom_item = remaining_qty_by_bom_item or {}

    for idx, item in enumerate(items, start=1):
        remaining_qty = remaining_qty_by_bom_item.get(
            item.id, (item.quantity or Decimal(0)) - (item.purchased_qty or Decimal(0))
        )
        if remaining_qty <= 0:
            continue

        item_data = calculate_order_item(item, idx, remaining_qty)
        order_items.append(item_data)

        total_amount += item_data["amount"]
        total_tax_amount += item_data["tax_amount"]
        total_amount_with_tax += item_data["amount_with_tax"]

    return order_items, total_amount, total_tax_amount, total_amount_with_tax


def create_order_preview(
    supplier: Vendor,
    supplier_id: int,
    bom: BomHeader,
    target_project_id: int,
    order_items: List[Dict[str, Any]],
    total_amount: Decimal,
    total_tax_amount: Decimal,
    total_amount_with_tax: Decimal,
    source_request_id: Optional[int] = None,
    source_mode: str = "BOM",
) -> Dict[str, Any]:
    """
    生成订单预览

    Returns:
        Dict[str, Any]: 订单预览数据
    """
    supplier_name = supplier.supplier_name if supplier else "未指定供应商"
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "project_id": target_project_id,
        "project_name": bom.project.project_name if bom.project else None,
        "order_type": "NORMAL",
        "order_title": f"{bom.bom_no} - {supplier_name}",
        "total_amount": float(total_amount),
        "tax_amount": float(total_tax_amount),
        "amount_with_tax": float(total_amount_with_tax),
        "item_count": len(order_items),
        "source_request_id": source_request_id,
        "source_mode": source_mode,
        "items": order_items,
    }


def create_purchase_order_from_preview(
    db: Session,
    order_preview: Dict[str, Any],
    bom: BomHeader,
    current_user_id: int,
    generate_order_no_func,
) -> Tuple[PurchaseOrder, List[PurchaseOrderItem]]:
    """
    根据预览创建实际的采购订单

    Returns:
        Tuple[PurchaseOrder, List[PurchaseOrderItem]]: (订单对象, 订单明细列表)
    """
    order_no = generate_order_no_func(db)

    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=order_preview["supplier_id"] or None,
        project_id=order_preview["project_id"],
        order_type=order_preview["order_type"],
        order_title=order_preview["order_title"],
        required_date=getattr(bom, "required_date", None),
        order_date=date.today(),
        status="DRAFT",
        total_amount=Decimal(str(order_preview["total_amount"])),
        tax_amount=Decimal(str(order_preview["tax_amount"])),
        amount_with_tax=Decimal(str(order_preview["amount_with_tax"])),
        created_by=current_user_id,
        source_request_id=order_preview.get("source_request_id"),
    )
    db.add(order)
    db.flush()

    order_items = []
    for item_data in order_preview["items"]:
        order_item = PurchaseOrderItem(
            order_id=order.id,
            item_no=item_data["item_no"],
            material_id=item_data["material_id"],
            bom_item_id=item_data["bom_item_id"],
            material_code=item_data["material_code"],
            material_name=item_data["material_name"],
            specification=item_data["specification"],
            unit=item_data["unit"],
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            amount=item_data["amount"],
            tax_rate=item_data["tax_rate"],
            tax_amount=item_data["tax_amount"],
            amount_with_tax=item_data["amount_with_tax"],
            required_date=item_data["required_date"],
            status="PENDING",
        )
        db.add(order_item)
        order_items.append(order_item)

    return order, order_items


def calculate_summary(purchase_orders_preview: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算汇总统计

    Returns:
        Dict[str, Any]: 汇总统计数据
    """
    return {
        "total_orders": len(purchase_orders_preview),
        "total_items": sum(len(order["items"]) for order in purchase_orders_preview),
        "total_amount": sum(order["total_amount"] for order in purchase_orders_preview),
        "total_amount_with_tax": sum(order["amount_with_tax"] for order in purchase_orders_preview),
    }


def _resolve_supplier(db: Session, supplier_id: int) -> Optional[Vendor]:
    if not supplier_id:
        return None
    return (
        db.query(Vendor)
        .filter(Vendor.id == supplier_id, Vendor.vendor_type == "MATERIAL")
        .first()
    )


def _load_existing_order_qty_by_bom_item(db: Session, bom_id: int) -> Dict[int, Decimal]:
    rows = (
        db.query(
            PurchaseOrderItem.bom_item_id,
            func.coalesce(func.sum(PurchaseOrderItem.quantity), 0),
        )
        .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
        .join(BomItem, BomItem.id == PurchaseOrderItem.bom_item_id)
        .filter(BomItem.bom_id == bom_id, PurchaseOrderItem.bom_item_id.isnot(None))
        .filter(~PurchaseOrder.status.in_(INACTIVE_ORDER_STATUSES))
        .group_by(PurchaseOrderItem.bom_item_id)
        .all()
    )
    return {bom_item_id: Decimal(str(total or 0)) for bom_item_id, total in rows}


def _load_existing_request_order_qty_map(db: Session, bom_id: int) -> Dict[Tuple[int, int], Decimal]:
    rows = (
        db.query(
            PurchaseOrder.source_request_id,
            PurchaseOrderItem.bom_item_id,
            func.coalesce(func.sum(PurchaseOrderItem.quantity), 0),
        )
        .join(PurchaseOrderItem, PurchaseOrderItem.order_id == PurchaseOrder.id)
        .join(BomItem, BomItem.id == PurchaseOrderItem.bom_item_id)
        .filter(
            BomItem.bom_id == bom_id,
            PurchaseOrder.source_request_id.isnot(None),
            PurchaseOrderItem.bom_item_id.isnot(None),
        )
        .filter(~PurchaseOrder.status.in_(INACTIVE_ORDER_STATUSES))
        .group_by(PurchaseOrder.source_request_id, PurchaseOrderItem.bom_item_id)
        .all()
    )
    return {
        (request_id, bom_item_id): Decimal(str(total or 0))
        for request_id, bom_item_id, total in rows
        if request_id and bom_item_id
    }


def _build_request_backed_order_previews(
    db: Session,
    bom: BomHeader,
    supplier_id: Optional[int],
) -> List[Dict[str, Any]]:
    request_items = (
        db.query(PurchaseRequestItem, PurchaseRequest)
        .join(PurchaseRequest, PurchaseRequest.id == PurchaseRequestItem.request_id)
        .filter(
            PurchaseRequest.source_type == "BOM",
            PurchaseRequest.source_id == bom.id,
            PurchaseRequestItem.bom_item_id.isnot(None),
        )
        .filter(~PurchaseRequest.status.in_(INACTIVE_REQUEST_STATUSES))
        .all()
    )
    if not request_items:
        return []

    bom_items = {
        item.id: item
        for item in db.query(BomItem).filter(BomItem.bom_id == bom.id, BomItem.id.isnot(None)).all()
    }
    existing_order_qty = _load_existing_request_order_qty_map(db, bom.id)
    grouped_lines: Dict[Tuple[int, int], List[Tuple[BomItem, Decimal]]] = defaultdict(list)

    for request_item, request in request_items:
        bom_item = bom_items.get(request_item.bom_item_id)
        if not bom_item:
            continue
        already_ordered = existing_order_qty.get((request.id, request_item.bom_item_id), Decimal(0))
        remaining_qty = Decimal(str(request_item.quantity or 0)) - already_ordered
        if remaining_qty <= 0:
            continue

        target_supplier_id = request.supplier_id or determine_supplier_for_item(db, bom_item, supplier_id) or 0
        grouped_lines[(request.id, target_supplier_id)].append((bom_item, remaining_qty))

    previews: List[Dict[str, Any]] = []
    for (source_request_id, target_supplier_id), lines in grouped_lines.items():
        remaining_qty_map = {item.id: qty for item, qty in lines}
        order_items, total_amount, total_tax_amount, total_amount_with_tax = build_order_items(
            [item for item, _ in lines],
            remaining_qty_by_bom_item=remaining_qty_map,
        )
        if not order_items:
            continue

        previews.append(
            create_order_preview(
                supplier=_resolve_supplier(db, target_supplier_id),
                supplier_id=target_supplier_id,
                bom=bom,
                target_project_id=bom.project_id,
                order_items=order_items,
                total_amount=total_amount,
                total_tax_amount=total_tax_amount,
                total_amount_with_tax=total_amount_with_tax,
                source_request_id=source_request_id,
                source_mode="REQUEST",
            )
        )

    return previews


def _build_direct_bom_order_previews(
    db: Session,
    bom: BomHeader,
    supplier_id: Optional[int],
) -> List[Dict[str, Any]]:
    purchase_items = get_purchase_items_from_bom(db, bom)
    existing_order_qty = _load_existing_order_qty_by_bom_item(db, bom.id)
    supplier_groups = group_items_by_supplier(db, purchase_items, supplier_id)

    previews: List[Dict[str, Any]] = []
    for grouped_supplier_id, items in supplier_groups.items():
        remaining_qty_map = {
            item.id: (item.quantity or Decimal(0)) - existing_order_qty.get(item.id, Decimal(0))
            for item in items
        }
        order_items, total_amount, total_tax_amount, total_amount_with_tax = build_order_items(
            items,
            remaining_qty_by_bom_item=remaining_qty_map,
        )
        if not order_items:
            continue

        previews.append(
            create_order_preview(
                supplier=_resolve_supplier(db, grouped_supplier_id),
                supplier_id=grouped_supplier_id,
                bom=bom,
                target_project_id=bom.project_id,
                order_items=order_items,
                total_amount=total_amount,
                total_tax_amount=total_tax_amount,
                total_amount_with_tax=total_amount_with_tax,
                source_mode="BOM",
            )
        )

    return previews


def preview_purchase_orders_from_bom(
    db: Session,
    bom: BomHeader,
    supplier_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    预览BOM采购订单：
    1. 若已有BOM采购需求，则优先基于采购需求生成订单预览
    2. 否则直接基于BOM剩余未下单数量生成
    """
    previews = _build_request_backed_order_previews(db, bom, supplier_id)
    source_mode = "request"
    if not previews:
        previews = _build_direct_bom_order_previews(db, bom, supplier_id)
        source_mode = "bom"

    return {
        "bom_id": bom.id,
        "source_mode": source_mode,
        "preview": previews,
        "summary": calculate_summary(previews),
    }


def sync_request_ordered_qty(db: Session, request_id: int) -> None:
    """把采购需求明细的 ordered_qty 同步成真实已下单数量。"""
    rows = (
        db.query(
            PurchaseOrderItem.bom_item_id,
            func.coalesce(func.sum(PurchaseOrderItem.quantity), 0),
        )
        .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
        .filter(
            PurchaseOrder.source_request_id == request_id,
            PurchaseOrderItem.bom_item_id.isnot(None),
        )
        .filter(~PurchaseOrder.status.in_(INACTIVE_ORDER_STATUSES))
        .group_by(PurchaseOrderItem.bom_item_id)
        .all()
    )
    ordered_qty_by_bom_item = {bom_item_id: Decimal(str(total or 0)) for bom_item_id, total in rows}

    request_items = db.query(PurchaseRequestItem).filter(PurchaseRequestItem.request_id == request_id).all()
    for request_item in request_items:
        request_item.ordered_qty = ordered_qty_by_bom_item.get(request_item.bom_item_id, Decimal(0))

    request = db.query(PurchaseRequest).filter(PurchaseRequest.id == request_id).first()
    if request:
        request.auto_po_created = all(
            (item.ordered_qty or Decimal(0)) >= (item.quantity or Decimal(0)) for item in request_items
        )
        if request.auto_po_created:
            request.auto_po_created_at = date.today()


def create_purchase_orders_from_bom(
    db: Session,
    bom: BomHeader,
    current_user_id: int,
    supplier_id: Optional[int],
    generate_order_no_func,
) -> Dict[str, Any]:
    preview = preview_purchase_orders_from_bom(db=db, bom=bom, supplier_id=supplier_id)
    created_orders: List[Dict[str, Any]] = []

    for order_preview in preview["preview"]:
        order, order_items = create_purchase_order_from_preview(
            db=db,
            order_preview=order_preview,
            bom=bom,
            current_user_id=current_user_id,
            generate_order_no_func=generate_order_no_func,
        )
        created_orders.append(
            {
                "id": order.id,
                "order_no": order.order_no,
                "supplier_id": order.supplier_id,
                "supplier_name": order_preview["supplier_name"],
                "item_count": len(order_items),
                "total_amount": float(order.total_amount or 0),
                "amount_with_tax": float(order.amount_with_tax or 0),
                "source_request_id": order.source_request_id,
            }
        )

        if order.source_request_id:
            sync_request_ordered_qty(db, order.source_request_id)

    return {
        "bom_id": bom.id,
        "source_mode": preview["source_mode"],
        "created_orders": created_orders,
        "summary": {
            "total_orders": len(created_orders),
            "total_items": sum(item["item_count"] for item in created_orders),
            "total_amount": sum(item["total_amount"] for item in created_orders),
            "total_amount_with_tax": sum(item["amount_with_tax"] for item in created_orders),
        },
    }
