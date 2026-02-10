# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务模块

聚合所有ECN BOM影响分析相关的服务，保持向后兼容
"""
from .analysis import analyze_bom_impact, analyze_single_bom
from .base import EcnBomAnalysisService
from .calculation import calculate_cost_impact, calculate_schedule_impact
from .cascade import analyze_cascade_impact
from .obsolete import calculate_obsolete_risk_level, check_obsolete_material_risk
from .utils import get_impact_description, save_bom_impact

__all__ = ["EcnBomAnalysisService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为方法添加到类中"""
    EcnBomAnalysisService.analyze_bom_impact = lambda self, ecn_id, machine_id=None, include_cascade=True: analyze_bom_impact(self, ecn_id, machine_id, include_cascade)
    EcnBomAnalysisService._analyze_single_bom = lambda self, ecn_id, bom_header, affected_materials, include_cascade=True: analyze_single_bom(self, ecn_id, bom_header, affected_materials, include_cascade)
    EcnBomAnalysisService.check_obsolete_material_risk = lambda self, ecn_id: check_obsolete_material_risk(self, ecn_id)

    # 以下为测试兼容的别名方法
    # get_impact_description 不需要 service 实例，但测试通过 self.method() 调用
    EcnBomAnalysisService._get_impact_description = lambda self, affected_mat: get_impact_description(affected_mat)
    # calculate_obsolete_risk_level 是纯函数，不需要 service 实例
    EcnBomAnalysisService._calculate_obsolete_risk_level = lambda self, obsolete_qty, obsolete_cost: calculate_obsolete_risk_level(obsolete_qty, obsolete_cost)
    # 以下函数以 service 为第一参数
    EcnBomAnalysisService._analyze_cascade_impact = lambda self, bom_items, affected_item_ids: analyze_cascade_impact(self, bom_items, affected_item_ids)
    EcnBomAnalysisService._calculate_cost_impact = lambda self, affected_materials, bom_items, affected_item_ids: calculate_cost_impact(self, affected_materials, bom_items, affected_item_ids)
    EcnBomAnalysisService._calculate_schedule_impact = lambda self, affected_materials, bom_items, affected_item_ids: calculate_schedule_impact(self, affected_materials, bom_items, affected_item_ids)
    EcnBomAnalysisService._save_bom_impact = lambda self, ecn_id, bom_version_id, machine_id, project_id, affected_item_count, total_cost_impact, schedule_impact_days, impact_analysis: save_bom_impact(self, ecn_id, bom_version_id, machine_id, project_id, affected_item_count, total_cost_impact, schedule_impact_days, impact_analysis)

_patch_methods()
