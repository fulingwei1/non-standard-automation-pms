# -*- coding: utf-8 -*-
"""
ECN分析相关 API endpoints - 路由聚合

已拆分为模块化结构：
- bom_impact.py: BOM影响分析（analyze, summary）
- obsolete_risk.py: 呆滞料风险（check, alerts）
- responsibility.py: 责任分摊（create, summary）
- rca_analysis.py: RCA分析（update, get）
- knowledge_base.py: 知识库集成和解决方案模板（extract, similar, recommend, templates）
"""

from fastapi import APIRouter

from . import bom_impact, knowledge_base, obsolete_risk, rca_analysis, responsibility

router = APIRouter()

# 聚合所有子路由
router.include_router(bom_impact.router)
router.include_router(obsolete_risk.router)
router.include_router(responsibility.router)
router.include_router(rca_analysis.router)
router.include_router(knowledge_base.router)
