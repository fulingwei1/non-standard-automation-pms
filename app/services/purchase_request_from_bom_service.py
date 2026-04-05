# -*- coding: utf-8 -*-
"""
从BOM生成采购需求服务
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem, Material
from app.models.purchase import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem
from app.models.vendor import Vendor

INACTIVE_REQUEST_STATUSES = {"CANCELLED", "REJECTED"}
INACTIVE_ORDER_STATUSES = {"CANCELLED", "REJECTED"}


def get_purchase_items_from_bom(bom: BomHeader) -> List[BomItem]:
    """
    获取BOM中需要采购的物料

    Returns:
        List[BomItem]: 需要采购的物料列表
    """
    return bom.items.filter(BomItem.source_type == "PURCHASE").all()


def determine_supplier_for_item(
    db: Session, item: BomItem, default_supplier_id: Optional[int]
) -> int:
    """
    确定物料的供应商ID

    Returns:
        int: 供应商ID（0表示未指定）
    """
    target_supplier_id = default_supplier_id

    if not target_supplier_id and item.supplier_id:
        target_supplier_id = item.supplier_id
    elif not target_supplier_id and item.material_id:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        if material and material.default_supplier_id:
            target_supplier_id = material.default_supplier_id

    return target_supplier_id if target_supplier_id else 0


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
        supplier_items[supplier_id].append(item)

    return supplier_items


def load_existing_request_qty_by_bom_item(db: Session, bom_id: int) -> Dict[int, Decimal]:
    """统计当前BOM已存在的有效采购需求数量。"""
    rows = (
        db.query(
            PurchaseRequestItem.bom_item_id,
            func.coalesce(func.sum(PurchaseRequestItem.quantity), 0),
        )
        .join(PurchaseRequest, PurchaseRequest.id == PurchaseRequestItem.request_id)
        .filter(
            PurchaseRequest.source_type == "BOM",
            PurchaseRequest.source_id == bom_id,
            PurchaseRequestItem.bom_item_id.isnot(None),
        )
        .filter(~PurchaseRequest.status.in_(INACTIVE_REQUEST_STATUSES))
        .group_by(PurchaseRequestItem.bom_item_id)
        .all()
    )
    return {bom_item_id: Decimal(str(total or 0)) for bom_item_id, total in rows}


def load_existing_direct_order_qty_by_bom_item(db: Session, bom_id: int) -> Dict[int, Decimal]:
    """统计当前BOM已存在的直采订单数量（不挂采购需求）。"""
    rows = (
        db.query(
            PurchaseOrderItem.bom_item_id,
            func.coalesce(func.sum(PurchaseOrderItem.quantity), 0),
        )
        .join(PurchaseOrder, PurchaseOrder.id == PurchaseOrderItem.order_id)
        .join(BomItem, BomItem.id == PurchaseOrderItem.bom_item_id)
        .filter(
            BomItem.bom_id == bom_id,
            PurchaseOrderItem.bom_item_id.isnot(None),
            PurchaseOrder.source_request_id.is_(None),
        )
        .filter(~PurchaseOrder.status.in_(INACTIVE_ORDER_STATUSES))
        .group_by(PurchaseOrderItem.bom_item_id)
        .all()
    )
    return {bom_item_id: Decimal(str(total or 0)) for bom_item_id, total in rows}


def build_request_items(
    items: List[BomItem],
    existing_requested_qty_by_bom_item: Optional[Dict[int, Decimal]] = None,
    existing_direct_order_qty_by_bom_item: Optional[Dict[int, Decimal]] = None,
) -> Tuple[List[Dict[str, Any]], Decimal]:
    """
    构建采购申请明细

    existing_requested_qty_by_bom_item: 已存在的采购需求数量（避免重复生成需求）
    existing_direct_order_qty_by_bom_item: 已存在的直采订单数量（避免先下单后又补需求）

    Returns:
        Tuple[List[Dict], Decimal]: (申请明细列表, 总金额)
    """
    request_items = []
    total_amount = Decimal(0)
    existing_requested_qty_by_bom_item = existing_requested_qty_by_bom_item or {}
    existing_direct_order_qty_by_bom_item = existing_direct_order_qty_by_bom_item or {}

    for item in items:
        covered_qty = existing_requested_qty_by_bom_item.get(item.id, Decimal(0)) + (
            existing_direct_order_qty_by_bom_item.get(item.id, Decimal(0))
        )
        fallback_purchased_qty = item.purchased_qty or Decimal(0)
        remaining_qty = (item.quantity or Decimal(0)) - max(covered_qty, fallback_purchased_qty)
        if remaining_qty <= 0:
            continue

        unit_price = item.unit_price or Decimal(0)
        amount = remaining_qty * unit_price
        total_amount += amount

        request_items.append(
            {
                "bom_item_id": item.id,
                "material_id": item.material_id,
                "material_code": item.material_code,
                "material_name": item.material_name,
                "specification": item.specification,
                "unit": item.unit or "件",
                "quantity": remaining_qty,
                "unit_price": unit_price,
                "amount": amount,
                "required_date": item.required_date,
                "is_key_item": item.is_key_item,
            }
        )

    return request_items, total_amount


def format_request_items(request_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    格式化申请明细（转换为可序列化的格式）

    Returns:
        List[Dict]: 格式化后的明细列表
    """
    return [
        {
            "bom_item_id": it["bom_item_id"],
            "material_id": it["material_id"],
            "material_code": it["material_code"],
            "material_name": it["material_name"],
            "specification": it["specification"],
            "unit": it["unit"],
            "quantity": float(it["quantity"]),
            "unit_price": float(it["unit_price"]),
            "amount": float(it["amount"]),
            "required_date": it["required_date"].isoformat() if it["required_date"] else None,
            "is_key_item": it["is_key_item"],
        }
        for it in request_items
    ]


def create_purchase_request(
    db: Session,
    bom: BomHeader,
    supplier_id: int,
    supplier_name: str,
    request_items: List[Dict[str, Any]],
    total_amount: Decimal,
    current_user_id: int,
    generate_request_no,
) -> PurchaseRequest:
    """
    创建采购申请

    Returns:
        PurchaseRequest: 创建的采购申请对象
    """
    request_no = generate_request_no(db)

    pr = PurchaseRequest(
        request_no=request_no,
        project_id=bom.project_id,
        machine_id=bom.machine_id,
        supplier_id=supplier_id if supplier_id != 0 else None,
        request_type="NORMAL",
        source_type="BOM",
        source_id=bom.id,
        request_reason=f"来自BOM {bom.bom_no} 的采购需求",
        required_date=getattr(bom, "required_date", None),
        status="DRAFT",
        total_amount=total_amount,
        created_by=current_user_id,
    )
    db.add(pr)
    db.flush()

    # 创建申请明细
    for it in request_items:
        pr_item = PurchaseRequestItem(
            request_id=pr.id,
            bom_item_id=it["bom_item_id"],
            material_id=it["material_id"],
            material_code=it["material_code"],
            material_name=it["material_name"],
            specification=it["specification"],
            unit=it["unit"],
            quantity=it["quantity"],
            unit_price=it["unit_price"],
            amount=it["amount"],
            required_date=it["required_date"],
        )
        db.add(pr_item)

    return pr


def _resolve_supplier_name(db: Session, supplier_id: int) -> str:
    if not supplier_id:
        return "未指定供应商"
    supplier = (
        db.query(Vendor)
        .filter(Vendor.id == supplier_id, Vendor.vendor_type == "MATERIAL")
        .first()
    )
    return supplier.supplier_name if supplier else "未指定供应商"


def preview_purchase_requests_from_bom(
    db: Session,
    bom: BomHeader,
    supplier_id: Optional[int] = None,
) -> Dict[str, Any]:
    """生成采购需求预览，并自动扣除已存在需求/直采订单，避免重复。"""
    purchase_items = get_purchase_items_from_bom(bom)
    existing_request_qty = load_existing_request_qty_by_bom_item(db, bom.id)
    existing_direct_order_qty = load_existing_direct_order_qty_by_bom_item(db, bom.id)
    supplier_groups = group_items_by_supplier(db, purchase_items, supplier_id)

    previews: List[Dict[str, Any]] = []
    for grouped_supplier_id, items in supplier_groups.items():
        request_items, total_amount = build_request_items(
            items,
            existing_requested_qty_by_bom_item=existing_request_qty,
            existing_direct_order_qty_by_bom_item=existing_direct_order_qty,
        )
        if not request_items:
            continue

        previews.append(
            {
                "supplier_id": grouped_supplier_id or 0,
                "supplier_name": _resolve_supplier_name(db, grouped_supplier_id or 0),
                "request_type": "NORMAL",
                "request_reason": f"来自BOM {bom.bom_no} 的采购需求",
                "item_count": len(request_items),
                "items": format_request_items(request_items),
                "total_amount": float(total_amount),
            }
        )

    return {
        "bom_id": bom.id,
        "purchase_requests": previews,
        "summary": {
            "total_requests": len(previews),
            "total_items": sum(len(item["items"]) for item in previews),
            "total_amount": sum(item["total_amount"] for item in previews),
        },
    }


def create_purchase_requests_from_bom(
    db: Session,
    bom: BomHeader,
    current_user_id: int,
    generate_request_no,
    supplier_id: Optional[int] = None,
) -> Dict[str, Any]:
    """按预览结果创建采购需求。"""
    preview = preview_purchase_requests_from_bom(db=db, bom=bom, supplier_id=supplier_id)
    created_requests = []

    for request_preview in preview["purchase_requests"]:
        raw_items = []
        total_amount = Decimal("0")
        for idx, item in enumerate(request_preview["items"], start=1):
            quantity = Decimal(str(item["quantity"]))
            unit_price = Decimal(str(item["unit_price"]))
            amount = Decimal(str(item["amount"]))
            total_amount += amount
            raw_items.append(
                {
                    "item_no": idx,
                    "bom_item_id": item["bom_item_id"],
                    "material_id": item["material_id"],
                    "material_code": item["material_code"],
                    "material_name": item["material_name"],
                    "specification": item["specification"],
                    "unit": item["unit"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "amount": amount,
                    "required_date": item["required_date"],
                    "is_key_item": item["is_key_item"],
                }
            )

        created = create_purchase_request(
            db=db,
            bom=bom,
            supplier_id=request_preview["supplier_id"],
            supplier_name=request_preview["supplier_name"],
            request_items=raw_items,
            total_amount=total_amount,
            current_user_id=current_user_id,
            generate_request_no=generate_request_no,
        )
        created_requests.append(
            {
                "id": created.id,
                "request_no": created.request_no,
                "supplier_id": created.supplier_id,
                "supplier_name": request_preview["supplier_name"],
                "item_count": len(raw_items),
                "total_amount": float(total_amount),
            }
        )

    return {
        "bom_id": bom.id,
        "created_requests": created_requests,
        "summary": {
            "total_requests": len(created_requests),
            "total_items": sum(item["item_count"] for item in created_requests),
            "total_amount": sum(item["total_amount"] for item in created_requests),
        },
    }
