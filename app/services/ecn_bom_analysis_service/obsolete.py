# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务 - 呆滞料检查
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from app.models.ecn import Ecn, EcnAffectedMaterial
from app.models.material import Material
from app.models.purchase import PurchaseOrder, PurchaseOrderItem


def check_obsolete_material_risk(
    service: "EcnBomAnalysisService",
    ecn_id: int
) -> Dict[str, Any]:
    """
    检查呆滞料风险

    Args:
        service: EcnBomAnalysisService实例
        ecn_id: ECN ID

    Returns:
        呆滞料风险分析结果
    """
    ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    affected_materials = service.db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id,
        EcnAffectedMaterial.change_type.in_(['DELETE', 'REPLACE'])
    ).all()

    if not affected_materials:
        return {
            "ecn_id": ecn_id,
            "has_obsolete_risk": False,
            "message": "没有删除或替换的物料"
        }

    obsolete_risks = []
    total_obsolete_cost = Decimal(0)

    for affected_mat in affected_materials:
        if not affected_mat.material_id:
            continue

        material = service.db.query(Material).filter(
            Material.id == affected_mat.material_id
        ).first()

        if not material:
            continue

        # 获取当前库存
        current_stock = Decimal(material.current_stock or 0)

        # 检查是否有在途采购订单
        po_items = service.db.query(PurchaseOrderItem).join(PurchaseOrder).filter(
            PurchaseOrderItem.material_id == material.id,
            PurchaseOrder.status.in_(['APPROVED', 'ORDERED', 'PARTIAL_RECEIVED'])
        ).all()

        in_transit_qty = sum(Decimal(item.quantity or 0) - Decimal(item.received_qty or 0)
                            for item in po_items)

        # 计算呆滞料数量
        obsolete_qty = current_stock + in_transit_qty
        obsolete_cost = obsolete_qty * Decimal(material.last_price or material.standard_price or 0)

        if obsolete_qty > 0:
            # 判断风险级别
            risk_level = calculate_obsolete_risk_level(obsolete_qty, obsolete_cost)

            obsolete_risks.append({
                "material_id": material.id,
                "material_code": material.material_code,
                "material_name": material.material_name,
                "current_stock": float(current_stock),
                "in_transit_qty": float(in_transit_qty),
                "obsolete_quantity": float(obsolete_qty),
                "obsolete_cost": float(obsolete_cost),
                "risk_level": risk_level,
                "change_type": affected_mat.change_type
            })

            total_obsolete_cost += obsolete_cost

            # 更新受影响物料的风险信息
            affected_mat.is_obsolete_risk = True
            affected_mat.obsolete_risk_level = risk_level
            affected_mat.obsolete_quantity = obsolete_qty
            affected_mat.obsolete_cost = obsolete_cost
            affected_mat.obsolete_analysis = (
                f"物料将被{'删除' if affected_mat.change_type == 'DELETE' else '替换'}，"
                f"当前库存{current_stock}，在途{in_transit_qty}，"
                f"预计呆滞{obsolete_qty}，成本{obsolete_cost:.2f}元"
            )

    service.db.commit()

    return {
        "ecn_id": ecn_id,
        "has_obsolete_risk": len(obsolete_risks) > 0,
        "total_obsolete_cost": float(total_obsolete_cost),
        "obsolete_risks": obsolete_risks,
        "analyzed_at": datetime.now().isoformat()
    }


def calculate_obsolete_risk_level(
    obsolete_qty: Decimal,
    obsolete_cost: Decimal
) -> str:
    """计算呆滞料风险级别"""
    # 风险级别判定规则
    if obsolete_cost >= 100000:  # 10万元以上
        return 'CRITICAL'
    elif obsolete_cost >= 50000:  # 5-10万元
        return 'HIGH'
    elif obsolete_cost >= 10000:  # 1-5万元
        return 'MEDIUM'
    else:  # 1万元以下
        return 'LOW'
