# -*- coding: utf-8 -*-
"""
ECN BOM影响分析服务模块

聚合所有ECN BOM影响分析相关的服务，保持向后兼容
"""
from .analysis import analyze_bom_impact, analyze_single_bom
from .base import EcnBomAnalysisService
from .obsolete import check_obsolete_material_risk

__all__ = ["EcnBomAnalysisService"]

# 将方法添加到类中，保持向后兼容
def _patch_methods():
    """将模块函数作为方法添加到类中"""
    EcnBomAnalysisService.analyze_bom_impact = lambda self, ecn_id, machine_id=None, include_cascade=True: analyze_bom_impact(self, ecn_id, machine_id, include_cascade)
    EcnBomAnalysisService._analyze_single_bom = lambda self, ecn_id, bom_header, affected_materials, include_cascade=True: analyze_single_bom(self, ecn_id, bom_header, affected_materials, include_cascade)
    EcnBomAnalysisService.check_obsolete_material_risk = lambda self, ecn_id: check_obsolete_material_risk(self, ecn_id)

_patch_methods()
