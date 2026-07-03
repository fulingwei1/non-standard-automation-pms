# -*- coding: utf-8 -*-
"""
齐套率计算工具函数
"""

from decimal import Decimal
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.material import BomItem
from app.services.purchase.in_transit import get_purchase_in_transit_qty


def calculate_kit_rate(
    db: Session, bom_items: List[BomItem], calculate_by: str = "quantity"  # "quantity" or "amount"
) -> Dict[str, Any]:
    """
    计算齐套率

    Args:
        bom_items: BOM明细列表
        calculate_by: 计算方式，"quantity"按数量，"amount"按金额

    Returns:
        包含齐套率统计信息的字典
    """
    total_items = len(bom_items)
    if total_items == 0:
        return {
            "total_items": 0,
            "fulfilled_items": 0,
            "shortage_items": 0,
            "in_transit_items": 0,
            "kit_rate": 0.0,
            "kit_status": "complete",
        }

    fulfilled_items = 0
    shortage_items = 0
    in_transit_items = 0
    total_quantity = Decimal(0)
    total_amount = Decimal(0)
    fulfilled_quantity = Decimal(0)
    fulfilled_amount = Decimal(0)

    for item in bom_items:
        # 当前齐套只看现有库存；received_qty 是采购到货进度字段，入库后已体现在库存中。
        material = item.material
        available_qty = Decimal(material.current_stock or 0) if material else Decimal(0)

        # 计算在途数量 = 已采购但未到货的数量
        in_transit_qty = get_purchase_in_transit_qty(db, item.material_id)

        # 需求数量
        required_qty = item.quantity or 0

        # 计算金额
        item_amount = required_qty * (item.unit_price or 0)
        total_amount += item_amount

        if calculate_by == "quantity":
            total_quantity += required_qty
            if available_qty >= required_qty:
                fulfilled_items += 1
                fulfilled_quantity += required_qty
            else:
                shortage_items += 1
                if in_transit_qty > 0:
                    in_transit_items += 1
        else:  # by amount
            total_quantity += required_qty
            if available_qty >= required_qty:
                fulfilled_items += 1
                fulfilled_quantity += required_qty
                fulfilled_amount += item_amount
            else:
                shortage_items += 1
                if in_transit_qty > 0:
                    in_transit_items += 1

    # 计算齐套率
    if calculate_by == "quantity":
        if total_quantity > 0:
            kit_rate = float((fulfilled_quantity / total_quantity) * 100)
        else:
            kit_rate = 0.0
    else:  # by amount
        if total_amount > 0:
            kit_rate = float((fulfilled_amount / total_amount) * 100)
        else:
            kit_rate = 0.0

    # 确定齐套状态
    if kit_rate >= 100:
        kit_status = "complete"
    elif kit_rate >= 80:
        kit_status = "partial"
    else:
        kit_status = "shortage"

    return {
        "total_items": total_items,
        "fulfilled_items": fulfilled_items,
        "shortage_items": shortage_items,
        "in_transit_items": in_transit_items,
        "kit_rate": round(kit_rate, 2),
        "kit_status": kit_status,
        "total_quantity": float(total_quantity),
        "fulfilled_quantity": float(fulfilled_quantity),
        "total_amount": float(total_amount),
        "fulfilled_amount": float(fulfilled_amount),
        "calculate_by": calculate_by,
    }
