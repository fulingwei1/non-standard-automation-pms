# -*- coding: utf-8 -*-
"""
从BOM创建采购订单服务
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem, Material
from app.models.vendor import Vendor
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


def get_purchase_items_from_bom(
    db: Session,
    bom: BomHeader
) -> List[BomItem]:
    """
    获取BOM中需要采购的物料

    Returns:
        List[BomItem]: 需要采购的BOM物料项列表
    """
    bom_items = bom.items.filter(
        BomItem.source_type == "PURCHASE"
    ).all()

    return bom_items


def determine_supplier_for_item(
    db: Session,
    item: BomItem,
    default_supplier_id: Optional[int]
) -> Optional[int]:
    """
    确定物料的供应商

    Returns:
        Optional[int]: 供应商ID，如果无法确定则返回None
    """
    # 优先使用提供的默认供应商
    if default_supplier_id:
        return default_supplier_id

    # 其次使用BOM项中的供应商
    if item.supplier_id:
        return item.supplier_id

    # 最后尝试从物料获取默认供应商
    if item.material_id:
        material = db.query(Material).filter(Material.id == item.material_id).first()
        if material and material.default_supplier_id:
            return material.default_supplier_id

    return None


def group_items_by_supplier(
    db: Session,
    bom_items: List[BomItem],
    default_supplier_id: Optional[int]
) -> Dict[int, List[BomItem]]:
    """
    按供应商分组物料

    Returns:
        Dict[int, List[BomItem]]: 供应商ID到物料列表的映射
    """
    supplier_items = defaultdict(list)

    for item in bom_items:
        supplier_id = determine_supplier_for_item(db, item, default_supplier_id)

        # 如果没有供应商，使用0表示未指定
        supplier_id = supplier_id or 0
        supplier_items[supplier_id].append(item)

    return dict(supplier_items)


def calculate_order_item(
    item: BomItem,
    item_no: int,
    remaining_qty: Decimal
) -> Dict[str, Any]:
    """
    计算订单明细项

    Returns:
        Dict[str, Any]: 订单明细项数据
    """
    unit_price = item.unit_price or Decimal(0)
    tax_rate = Decimal(13)  # 默认税率13%
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
    items: List[BomItem]
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

    for idx, item in enumerate(items, start=1):
        # 计算未采购数量
        remaining_qty = item.quantity - (item.purchased_qty or 0)
        if remaining_qty <= 0:
            continue  # 跳过已完全采购的物料

        item_data = calculate_order_item(item, idx, remaining_qty)
        order_items.append(item_data)

        total_amount += item_data["amount"]
        total_tax_amount += item_data["tax_amount"]
        total_amount_with_tax += item_data["amount_with_tax"]

    return order_items, total_amount, total_tax_amount, total_amount_with_tax


def create_order_preview(
    supplier: Supplier,
    supplier_id: int,
    bom: BomHeader,
    target_project_id: int,
    order_items: List[Dict[str, Any]],
    total_amount: Decimal,
    total_tax_amount: Decimal,
    total_amount_with_tax: Decimal
) -> Dict[str, Any]:
    """
    生成订单预览

    Returns:
        Dict[str, Any]: 订单预览数据
    """
    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.supplier_name,
        "project_id": target_project_id,
        "project_name": bom.project.project_name if bom.project else None,
        "order_type": "NORMAL",
        "order_title": f"{bom.bom_no} - {supplier.supplier_name}",
        "total_amount": float(total_amount),
        "tax_amount": float(total_tax_amount),
        "amount_with_tax": float(total_amount_with_tax),
        "item_count": len(order_items),
        "items": order_items,
    }


def create_purchase_order_from_preview(
    db: Session,
    order_preview: Dict[str, Any],
    bom: BomHeader,
    current_user_id: int,
    generate_order_no_func
) -> Tuple[PurchaseOrder, List[PurchaseOrderItem]]:
    """
    根据预览创建实际的采购订单

    Returns:
        Tuple[PurchaseOrder, List[PurchaseOrderItem]]: (订单对象, 订单明细列表)
    """
    # 生成订单编号
    order_no = generate_order_no_func(db)

    # 创建订单
    order = PurchaseOrder(
        order_no=order_no,
        supplier_id=order_preview["supplier_id"],
        project_id=order_preview["project_id"],
        order_type=order_preview["order_type"],
        order_title=order_preview["order_title"],
        required_date=bom.required_date if hasattr(bom, 'required_date') else None,
        order_date=date.today(),
        status="DRAFT",
        total_amount=Decimal(str(order_preview["total_amount"])),
        tax_amount=Decimal(str(order_preview["tax_amount"])),
        amount_with_tax=Decimal(str(order_preview["amount_with_tax"])),
        created_by=current_user_id,
    )
    db.add(order)
    db.flush()

    # 创建订单明细
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


def calculate_summary(
    purchase_orders_preview: List[Dict[str, Any]]
) -> Dict[str, Any]:
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
