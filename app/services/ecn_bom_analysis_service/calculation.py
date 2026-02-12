# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务 - 计算功能
"""
from decimal import Decimal
from typing import TYPE_CHECKING, List, Set

from app.models.ecn import EcnAffectedMaterial
from app.models.material import BomItem, Material

if TYPE_CHECKING:
    from app.services.ecn_bom_analysis_service import EcnBomAnalysisService


def calculate_cost_impact(
    service: "EcnBomAnalysisService",
    affected_materials: List[EcnAffectedMaterial],
    bom_items: List[BomItem],
    affected_item_ids: Set[int]
) -> Decimal:
    """计算成本影响"""
    total_impact = Decimal(0)

    # 从受影响物料中获取成本影响
    for affected_mat in affected_materials:
        if affected_mat.cost_impact:
            total_impact += Decimal(affected_mat.cost_impact)

    # 从BOM项中计算变更成本
    for item_id in affected_item_ids:
        bom_item = next((item for item in bom_items if item.id == item_id), None)
        if bom_item and bom_item.amount:
            # 如果物料被删除，成本影响为负
            affected_mat = next(
                (am for am in affected_materials
                 if am.material_code == bom_item.material_code or
                    am.material_id == bom_item.material_id),
                None
            )
            if affected_mat and affected_mat.change_type == 'DELETE':
                total_impact -= Decimal(bom_item.amount)
            elif affected_mat and affected_mat.change_type == 'ADD':
                # 新增物料的成本需要从新规格中获取
                if affected_mat.cost_impact:
                    total_impact += Decimal(affected_mat.cost_impact)

    return total_impact


def calculate_schedule_impact(
    service: "EcnBomAnalysisService",
    affected_materials: List[EcnAffectedMaterial],
    bom_items: List[BomItem],
    affected_item_ids: Set[int]
) -> int:
    """计算交期影响（天数）"""
    max_impact_days = 0

    for item_id in affected_item_ids:
        bom_item = next((item for item in bom_items if item.id == item_id), None)
        if not bom_item:
            continue

        # 获取物料信息
        material = service.db.query(Material).filter(
            Material.id == bom_item.material_id
        ).first()

        if material and material.lead_time_days:
            # 如果物料变更，可能需要重新采购，影响交期
            affected_mat = next(
                (am for am in affected_materials
                 if am.material_code == bom_item.material_code or
                    am.material_id == bom_item.material_id),
                None
            )

            if affected_mat:
                # 变更类型影响交期
                if affected_mat.change_type in ['UPDATE', 'REPLACE']:
                    # 更新或替换可能需要重新采购
                    max_impact_days = max(max_impact_days, material.lead_time_days)
                elif affected_mat.change_type == 'ADD':
                    # 新增物料需要采购周期
                    max_impact_days = max(max_impact_days, material.lead_time_days)

    return max_impact_days
