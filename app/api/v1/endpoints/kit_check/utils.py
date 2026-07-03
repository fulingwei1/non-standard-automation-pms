# -*- coding: utf-8 -*-
"""
齐套检查工具函数
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.common.query_filters import apply_like_filter
from app.models.material import BomHeader, BomItem
from app.models.production import WorkOrder
from app.models.project import Machine
from app.models.shortage import KitCheck
from app.services.purchase.in_transit import get_purchase_in_transit_qty


def generate_check_no(db: Session) -> str:
    """生成齐套检查编号：KC-yymmdd-xxx"""
    today = datetime.now().strftime("%y%m%d")
    max_check_query = db.query(KitCheck)
    max_check_query = apply_like_filter(
        max_check_query,
        KitCheck,
        f"KC-{today}-%",
        "check_no",
        use_ilike=False,
    )
    max_check = max_check_query.order_by(desc(KitCheck.check_no)).first()
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
        in_transit_qty = get_purchase_in_transit_qty(db, item.material_id)

        # 需求数量 = BOM用量 * 工单计划数量
        required_qty = Decimal(item.quantity or 0) * Decimal(work_order.plan_qty or 1)

        if available_qty >= required_qty:
            fulfilled_items += 1
        else:
            shortage_items += 1
            if in_transit_qty > 0:
                in_transit_items += 1
            shortage_details.append(
                {
                    "material_id": material.id,
                    "material_code": material.material_code,
                    "material_name": material.material_name,
                    "required_qty": float(required_qty),
                    "available_qty": float(available_qty),
                    "in_transit_qty": float(in_transit_qty),
                    "shortage_qty": float(required_qty - available_qty),
                    "status": "partial" if available_qty > 0 else "shortage",
                }
            )

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
