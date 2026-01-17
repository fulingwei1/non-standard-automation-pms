# -*- coding: utf-8 -*-
"""
齐套检查工具函数
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.material import BomHeader, BomItem
from app.models.production import WorkOrder
from app.models.project import Machine
from app.models.purchase import PurchaseOrderItem
from app.models.shortage import KitCheck


def generate_check_no(db: Session) -> str:
    """生成齐套检查编号：KC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_check = (
        db.query(KitCheck)
        .filter(KitCheck.check_no.like(f"KC-{today}-%"))
        .order_by(desc(KitCheck.check_no))
        .first()
    )
    if max_check:
        seq = int(max_check.check_no.split("-")[-1]) + 1
    else:
        seq = 1
    return f"KC-{today}-{seq:03d}"


def calculate_work_order_kit_rate(
    db: Session,
    work_order: WorkOrder,
) -> Dict[str, Any]:
    """
    计算工单齐套率

    Args:
        db: 数据库会话
        work_order: 工单对象

    Returns:
        包含齐套率统计信息的字典
    """
    # 获取工单关联的机台BOM
    bom_items = []
    if work_order.machine_id:
        machine = db.query(Machine).filter(Machine.id == work_order.machine_id).first()
        if machine and machine.bom_id:
            bom_header = db.query(BomHeader).filter(BomHeader.id == machine.bom_id).first()
            if bom_header:
                bom_items = db.query(BomItem).filter(BomItem.bom_id == bom_header.id).all()

    if not bom_items:
        return {
            "total_items": 0,
            "fulfilled_items": 0,
            "shortage_items": 0,
            "in_transit_items": 0,
            "kit_rate": 0.0,
            "kit_status": "shortage",
            "is_kit_complete": False,
            "shortage_details": [],
        }

    total_items = len(bom_items)
    fulfilled_items = 0
    shortage_items = 0
    in_transit_items = 0
    shortage_details = []

    for item in bom_items:
        material = item.material
        if not material:
            continue

        # 计算可用数量 = 当前库存
        available_qty = Decimal(material.current_stock or 0)

        # 计算在途数量 = 已采购但未到货的数量
        in_transit_qty = Decimal(0)
        po_items = (
            db.query(PurchaseOrderItem)
            .filter(PurchaseOrderItem.material_id == item.material_id)
            .filter(PurchaseOrderItem.status.in_(["APPROVED", "ORDERED", "PARTIAL_RECEIVED"]))
            .all()
        )
        for po_item in po_items:
            in_transit_qty += (Decimal(po_item.quantity or 0) - Decimal(po_item.received_qty or 0))

        # 总可用数量 = 可用数量 + 在途数量
        total_available = available_qty + in_transit_qty

        # 需求数量 = BOM用量 * 工单计划数量
        required_qty = Decimal(item.quantity or 0) * Decimal(work_order.plan_qty or 1)

        if total_available >= required_qty:
            fulfilled_items += 1
        elif total_available > 0:
            in_transit_items += 1
            shortage_details.append({
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.material_name,
                "required_qty": float(required_qty),
                "available_qty": float(available_qty),
                "in_transit_qty": float(in_transit_qty),
                "shortage_qty": float(required_qty - total_available),
                "status": "partial",
            })
        else:
            shortage_items += 1
            shortage_details.append({
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.material_name,
                "required_qty": float(required_qty),
                "available_qty": float(available_qty),
                "in_transit_qty": float(in_transit_qty),
                "shortage_qty": float(required_qty),
                "status": "shortage",
            })

    # 计算齐套率
    kit_rate = (fulfilled_items / total_items * 100) if total_items > 0 else 0.0

    # 确定齐套状态
    if fulfilled_items == total_items:
        kit_status = "complete"
        is_kit_complete = True
    elif fulfilled_items > 0:
        kit_status = "partial"
        is_kit_complete = False
    else:
        kit_status = "shortage"
        is_kit_complete = False

    return {
        "total_items": total_items,
        "fulfilled_items": fulfilled_items,
        "shortage_items": shortage_items,
        "in_transit_items": in_transit_items,
        "kit_rate": round(float(kit_rate), 2),
        "kit_status": kit_status,
        "is_kit_complete": is_kit_complete,
        "shortage_details": shortage_details,
    }
