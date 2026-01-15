# -*- coding: utf-8 -*-
"""
装配套件 API - 模块化结构
"""

from fastapi import APIRouter

from .stages import router as stages_router
from .material_mapping import router as material_mapping_router
from .bom_attributes import router as bom_attributes_router
from .kit_analysis import router as kit_analysis_router
from .shortage_alerts import router as shortage_alerts_router
from .alert_rules import router as alert_rules_router
from .wechat_config import router as wechat_config_router
from .scheduling import router as scheduling_router
from .dashboard import router as dashboard_router
from .templates import router as templates_router

router = APIRouter()

router.include_router(stages_router)
router.include_router(material_mapping_router)
router.include_router(bom_attributes_router)
router.include_router(kit_analysis_router)
router.include_router(shortage_alerts_router)
router.include_router(alert_rules_router)
router.include_router(wechat_config_router)
router.include_router(scheduling_router)
router.include_router(dashboard_router)
router.include_router(templates_router)

__all__ = ['router']
