# -*- coding: utf-8 -*-
"""
机台级齐套率端点
"""

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.material import BomHeader
from app.models.project import Machine
from app.models.purchase import PurchaseOrderItem
from app.models.user import User

from .utils import calculate_kit_rate

router = APIRouter()


@router.get("/machines/{machine_id}/kit-rate")
def get_machine_kit_rate(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    calculate_by: str = Query("quantity", description="计算方式：quantity(数量) 或 amount(金额)"),
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    计算机台齐套率
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    if calculate_by not in ["quantity", "amount"]:
        raise HTTPException(status_code=400, detail="calculate_by 必须是 quantity 或 amount")

    # 获取机台的最新BOM
    bom = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .filter(BomHeader.is_latest == True)
        .first()
    )

    if not bom:
        raise HTTPException(status_code=404, detail="机台没有BOM")

    bom_items = bom.items.all()
    kit_rate = calculate_kit_rate(db, bom_items, calculate_by)

    return {
        "machine_id": machine_id,
        "machine_no": machine.machine_no,
        "machine_name": machine.machine_name,
        "bom_id": bom.id,
        "bom_no": bom.bom_no,
        "bom_name": bom.bom_name,
        **kit_rate,
    }


@router.get("/machines/{machine_id}/material-status")
def get_machine_material_status(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    current_user: User = Depends(security.require_procurement_access()),
) -> Any:
    """
    获取机台物料状态（详细到货状态）
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 获取机台的最新BOM
    bom = (
        db.query(BomHeader)
        .filter(BomHeader.machine_id == machine_id)
        .filter(BomHeader.is_latest == True)
        .first()
    )

    if not bom:
        raise HTTPException(status_code=404, detail="机台没有BOM")

    bom_items = bom.items.all()
    material_status_list = []

    for item in bom_items:
        material = item.material
        required_qty = item.quantity or 0

        # 当前库存
        current_stock = material.current_stock or 0 if material else 0

        # 已到货数量
        received_qty = item.received_qty or 0

        # 可用数量
        available_qty = current_stock + received_qty

        # 在途数量
        in_transit_qty = Decimal(0)
        if item.material_id:
            po_items = (
                db.query(PurchaseOrderItem)
                .filter(PurchaseOrderItem.material_id == item.material_id)
                .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
                .all()
            )
            for po_item in po_items:
                in_transit_qty += (po_item.quantity or 0) - (po_item.received_qty or 0)

        # 总可用数量
        total_available = available_qty + in_transit_qty

        # 短缺数量
        shortage_qty = max(0, required_qty - total_available)

        # 状态
        if total_available >= required_qty:
            status = "fulfilled"
        elif total_available > 0:
            status = "partial"
        else:
            status = "shortage"

        material_status_list.append({
            "bom_item_id": item.id,
            "item_no": item.item_no,
            "material_id": item.material_id,
            "material_code": item.material_code,
            "material_name": item.material_name,
            "specification": item.specification,
            "unit": item.unit,
            "required_qty": float(required_qty),
            "current_stock": float(current_stock),
            "received_qty": float(received_qty),
            "available_qty": float(available_qty),
            "in_transit_qty": float(in_transit_qty),
            "total_available": float(total_available),
            "shortage_qty": float(shortage_qty),
            "status": status,
            "is_key_item": item.is_key_item,
            "required_date": item.required_date.isoformat() if item.required_date else None,
        })

    return {
        "machine_id": machine_id,
        "machine_no": machine.machine_no,
        "machine_name": machine.machine_name,
        "bom_id": bom.id,
        "bom_no": bom.bom_no,
        "items": material_status_list,
    }
