# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务 - 主要分析功能
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.models.ecn import Ecn, EcnAffectedMaterial
from app.models.material import BomHeader, BomItem
from app.models.project import Machine

from .calculation import calculate_cost_impact, calculate_schedule_impact
from .cascade import analyze_cascade_impact
from .utils import get_impact_description, save_bom_impact


def analyze_bom_impact(
    service: "EcnBomAnalysisService",
    ecn_id: int,
    machine_id: Optional[int] = None,
    include_cascade: bool = True
) -> Dict[str, Any]:
    """
    分析ECN对BOM的影响

    Args:
        service: EcnBomAnalysisService实例
        ecn_id: ECN ID
        machine_id: 设备ID（可选，如果ECN已关联设备则自动获取）
        include_cascade: 是否包含级联影响分析

    Returns:
        分析结果字典
    """
    ecn = service.db.query(Ecn).filter(Ecn.id == ecn_id).first()
    if not ecn:
        raise ValueError(f"ECN {ecn_id} 不存在")

    # 获取设备ID
    if not machine_id:
        machine_id = ecn.machine_id

    if not machine_id:
        raise ValueError("需要指定设备ID或ECN必须关联设备")

    # 获取受影响的物料
    affected_materials = service.db.query(EcnAffectedMaterial).filter(
        EcnAffectedMaterial.ecn_id == ecn_id
    ).all()

    if not affected_materials:
        return {
            "ecn_id": ecn_id,
            "machine_id": machine_id,
            "has_impact": False,
            "message": "没有受影响的物料"
        }

    # 获取设备的BOM
    machine = service.db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise ValueError(f"设备 {machine_id} 不存在")

    bom_headers = service.db.query(BomHeader).filter(
        BomHeader.machine_id == machine_id,
        BomHeader.status == 'RELEASED',
        BomHeader.is_latest
    ).all()

    if not bom_headers:
        return {
            "ecn_id": ecn_id,
            "machine_id": machine_id,
            "has_impact": False,
            "message": "设备没有已发布的BOM"
        }

    # 分析每个BOM的影响
    bom_impacts = []
    total_cost_impact = Decimal(0)
    total_affected_items = 0
    max_schedule_impact = 0

    for bom_header in bom_headers:
        impact_result = analyze_single_bom(
            service=service,
            ecn_id=ecn_id,
            bom_header=bom_header,
            affected_materials=affected_materials,
            include_cascade=include_cascade
        )

        if impact_result["has_impact"]:
            bom_impacts.append(impact_result)
            total_cost_impact += Decimal(impact_result.get("cost_impact", 0))
            total_affected_items += impact_result.get("affected_item_count", 0)
            max_schedule_impact = max(
                max_schedule_impact,
                impact_result.get("schedule_impact_days", 0)
            )

    # 保存分析结果
    for bom_header in bom_headers:
        save_bom_impact(
            service=service,
            ecn_id=ecn_id,
            bom_version_id=bom_header.id,
            machine_id=machine_id,
            project_id=ecn.project_id,
            affected_item_count=total_affected_items,
            total_cost_impact=total_cost_impact,
            schedule_impact_days=max_schedule_impact,
            impact_analysis={
                "bom_impacts": bom_impacts,
                "analysis_time": datetime.now().isoformat()
            }
        )

    return {
        "ecn_id": ecn_id,
        "machine_id": machine_id,
        "project_id": ecn.project_id,
        "has_impact": len(bom_impacts) > 0,
        "total_cost_impact": float(total_cost_impact),
        "total_affected_items": total_affected_items,
        "max_schedule_impact_days": max_schedule_impact,
        "bom_impacts": bom_impacts,
        "analyzed_at": datetime.now().isoformat()
    }


def analyze_single_bom(
    service: "EcnBomAnalysisService",
    ecn_id: int,
    bom_header: BomHeader,
    affected_materials: List[EcnAffectedMaterial],
    include_cascade: bool = True
) -> Dict[str, Any]:
    """分析单个BOM的影响"""
    # 获取BOM所有物料项
    bom_items = service.db.query(BomItem).filter(
        BomItem.bom_id == bom_header.id
    ).all()

    # 构建物料编码到BOM项的映射
    material_code_to_items = {}
    material_id_to_items = {}
    for item in bom_items:
        if item.material_code:
            if item.material_code not in material_code_to_items:
                material_code_to_items[item.material_code] = []
            material_code_to_items[item.material_code].append(item)
        if item.material_id:
            if item.material_id not in material_id_to_items:
                material_id_to_items[item.material_id] = []
            material_id_to_items[item.material_id].append(item)

    # 分析直接影响
    direct_impact = []
    affected_item_ids = set()

    for affected_mat in affected_materials:
        # 通过物料编码匹配
        if affected_mat.material_code in material_code_to_items:
            for bom_item in material_code_to_items[affected_mat.material_code]:
                affected_item_ids.add(bom_item.id)
                direct_impact.append({
                    "bom_item_id": bom_item.id,
                    "material_code": bom_item.material_code,
                    "material_name": bom_item.material_name,
                    "change_type": affected_mat.change_type,
                    "impact": get_impact_description(affected_mat)
                })

        # 通过物料ID匹配
        if affected_mat.material_id and affected_mat.material_id in material_id_to_items:
            for bom_item in material_id_to_items[affected_mat.material_id]:
                if bom_item.id not in affected_item_ids:
                    affected_item_ids.add(bom_item.id)
                    direct_impact.append({
                        "bom_item_id": bom_item.id,
                        "material_code": bom_item.material_code,
                        "material_name": bom_item.material_name,
                        "change_type": affected_mat.change_type,
                        "impact": get_impact_description(affected_mat)
                    })

    # 分析级联影响
    cascade_impact = []
    if include_cascade:
        cascade_impact = analyze_cascade_impact(
            service=service,
            bom_items=bom_items,
            affected_item_ids=affected_item_ids
        )

    # 计算成本影响
    cost_impact = calculate_cost_impact(
        service=service,
        affected_materials=affected_materials,
        bom_items=bom_items,
        affected_item_ids=affected_item_ids
    )

    # 计算交期影响
    schedule_impact = calculate_schedule_impact(
        service=service,
        affected_materials=affected_materials,
        bom_items=bom_items,
        affected_item_ids=affected_item_ids
    )

    return {
        "bom_id": bom_header.id,
        "bom_no": bom_header.bom_no,
        "bom_name": bom_header.bom_name,
        "has_impact": len(direct_impact) > 0 or len(cascade_impact) > 0,
        "direct_impact": direct_impact,
        "cascade_impact": cascade_impact,
        "affected_item_count": len(affected_item_ids) + len(cascade_impact),
        "cost_impact": float(cost_impact),
        "schedule_impact_days": schedule_impact
    }
