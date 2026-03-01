# -*- coding: utf-8 -*-
"""
装配套件 API - 模块化结构
"""

from fastapi import APIRouter

from .alert_rules import router as alert_rules_router
from .bom_attributes import router as bom_attributes_router
from .bom_attributes import smart_recommend_assembly_attrs
from .dashboard import router as dashboard_router

# Compatibility exports for unit/integration tests
from .kit_analysis.analysis import execute_kit_analysis
from .kit_analysis import router as kit_analysis_router
from .material_mapping import router as material_mapping_router
from .scheduling import generate_scheduling_suggestions
from .scheduling import router as scheduling_router
from .shortage_alerts import router as shortage_alerts_router
from .stages import router as stages_router
from .templates import router as templates_router
from .kit_rate import router as kit_rate_router
from .wechat_config import router as wechat_config_router

router = APIRouter()

router.include_router(stages_router)
router.include_router(material_mapping_router)
router.include_router(bom_attributes_router)
router.include_router(kit_analysis_router, prefix="/assembly-kit/kit-analysis", tags=["kit_analysis"])
router.include_router(shortage_alerts_router)
router.include_router(alert_rules_router)
router.include_router(wechat_config_router)
router.include_router(scheduling_router)
router.include_router(dashboard_router)
router.include_router(templates_router)
router.include_router(kit_rate_router, prefix="/kit-rate", tags=["kit-rate"])

__all__ = [
    "router",
    "execute_kit_analysis",
    "smart_recommend_assembly_attrs",
    "generate_scheduling_suggestions",
]
