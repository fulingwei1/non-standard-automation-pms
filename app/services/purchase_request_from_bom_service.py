# -*- coding: utf-8 -*-
"""
从BOM生成采购需求服务
"""

from typing import Dict, Any, List, Optional
from decimal import Decimal
from collections import defaultdict
from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem, Material, Supplier
from app.models.purchase import PurchaseRequest, PurchaseRequestItem


def get_purchase_items_from_bom(bom: BomHeader) -> List[BomItem]:
    """
    获取BOM中需要采购的物料
    
    Returns:
        List[BomItem]: 需要采购的物料列表
    """
    return bom.items.filter(BomItem.source_type == "PURCHASE").all()


def determine_supplier_for_item(
    db: Session,
    item: BomItem,
    default_supplier_id: Optional[int]
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
        supplier_items[supplier_id].append(item)
    
    return supplier_items


def build_request_items(items: List[BomItem]) -> tuple[List[Dict[str, Any]], Decimal]:
    """
    构建采购申请明细
    
    Returns:
        Tuple[List[Dict], Decimal]: (申请明细列表, 总金额)
    """
    request_items = []
    total_amount = Decimal(0)
    
    for item in items:
        remaining_qty = (item.quantity or Decimal(0)) - (item.purchased_qty or Decimal(0))
        if remaining_qty <= 0:
            continue
        
        unit_price = item.unit_price or Decimal(0)
        amount = remaining_qty * unit_price
        total_amount += amount
        
        request_items.append({
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
        })
    
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
    generate_request_no
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
        required_date=bom.required_date,
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
