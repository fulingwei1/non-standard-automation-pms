# -*- coding: utf-8 -*-
"""
gate_s5_s6 阶段门检查

包含gate_s5_s6相关的阶段门校验逻辑
"""

"""
项目模块 - 阶段门检查函数

包含所有阶段门校验逻辑（S1→S2 到 S8→S9）
"""

from decimal import Decimal
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from app.models.project import Machine, Project, ProjectPaymentPlan



def check_gate_s5_to_s6(db: Session, project: Project) -> Tuple[bool, List[str]]:
    """G5: S5→S6 阶段门校验 - 关键物料齐套率≥80%"""
    missing = []

    machines = db.query(Machine).filter(Machine.project_id == project.id).all()

    if not machines:
        missing.append("项目下没有机台")
        return (False, missing)

    from app.api.v1.endpoints.kit_rate import calculate_kit_rate
    from app.models.material import BomHeader, BomItem

    for machine in machines:
        bom = db.query(BomHeader).filter(
            BomHeader.machine_id == machine.id,
            BomHeader.status == "RELEASED"
        ).first()

        if not bom:
            missing.append(f"机台 {machine.machine_code} 的BOM未发布")
            continue

        bom_items = db.query(BomItem).filter(BomItem.bom_id == bom.id).all()

        if not bom_items:
            continue

        kit_result = calculate_kit_rate(db, bom_items, calculate_by="quantity")
        kit_rate = kit_result.get("kit_rate", 0)

        if kit_rate < 80:
            missing.append(f"机台 {machine.machine_code} 物料齐套率 {kit_rate:.1f}%，需≥80%")

        # 检查关键物料已到货
        for item in bom_items:
            material = item.material
            if material and (material.is_key_material or material.material_category in ["关键件", "核心件", "KEY"]):
                available_qty = Decimal(str(material.current_stock or 0)) + Decimal(str(item.received_qty or 0))
                required_qty = Decimal(str(item.quantity or 0))

                if available_qty < required_qty:
                    missing.append(f"关键物料 {material.material_name} 未到货（需求：{required_qty}，可用：{available_qty}）")

        # 检查外协件已完成
        from app.models.outsourcing import OutsourcingOrder
        outsourcing_orders = db.query(OutsourcingOrder).filter(
            OutsourcingOrder.project_id == project.id,
            OutsourcingOrder.machine_id == machine.id if machine else None
        ).all()

        if outsourcing_orders:
            for order in outsourcing_orders:
                if order.status not in ["COMPLETED", "CLOSED"]:
                    total_ordered = sum(float(item.order_quantity or 0) for item in order.items)
                    total_delivered = sum(float(item.delivered_quantity or 0) for item in order.items)

                    if total_delivered < total_ordered:
                        missing.append(f"外协订单 {order.order_no} 未完成（已交付：{total_delivered}，需求：{total_ordered}）")

    return (len(missing) == 0, missing)


