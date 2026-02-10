# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务 - 工具函数
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from app.models.ecn import EcnAffectedMaterial, EcnBomImpact


def get_impact_description(affected_mat: EcnAffectedMaterial) -> str:
    """获取影响描述"""
    change_type_map = {
        'ADD': '新增',
        'DELETE': '删除',
        'UPDATE': '修改',
        'REPLACE': '替换'
    }

    desc = change_type_map.get(affected_mat.change_type, affected_mat.change_type)

    if affected_mat.old_quantity is not None and affected_mat.new_quantity is not None:
        desc += f"（数量：{affected_mat.old_quantity} → {affected_mat.new_quantity}）"
    elif getattr(affected_mat, 'old_specification', None) and getattr(affected_mat, 'new_specification', None):
        desc += "（规格变更）"

    return desc


def save_bom_impact(
    service: "EcnBomAnalysisService",
    ecn_id: int,
    bom_version_id: int,
    machine_id: int,
    project_id: int,
    affected_item_count: int,
    total_cost_impact: Decimal,
    schedule_impact_days: int,
    impact_analysis: Dict[str, Any]
):
    """保存BOM影响分析结果"""
    # 检查是否已存在
    existing = service.db.query(EcnBomImpact).filter(
        EcnBomImpact.ecn_id == ecn_id,
        EcnBomImpact.bom_version_id == bom_version_id
    ).first()

    if existing:
        # 更新
        existing.affected_item_count = affected_item_count
        existing.total_cost_impact = total_cost_impact
        existing.schedule_impact_days = schedule_impact_days
        existing.impact_analysis = impact_analysis
        existing.analysis_status = 'COMPLETED'
        existing.analyzed_at = datetime.now()
    else:
        # 创建
        bom_impact = EcnBomImpact(
            ecn_id=ecn_id,
            bom_version_id=bom_version_id,
            machine_id=machine_id,
            project_id=project_id,
            affected_item_count=affected_item_count,
            total_cost_impact=total_cost_impact,
            schedule_impact_days=schedule_impact_days,
            impact_analysis=impact_analysis,
            analysis_status='COMPLETED',
            analyzed_at=datetime.now()
        )
        service.db.add(bom_impact)

    service.db.commit()
