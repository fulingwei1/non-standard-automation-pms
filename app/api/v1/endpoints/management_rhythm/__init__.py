# -*- coding: utf-8 -*-
"""
管理节律 API - 模块化结构
"""

from fastapi import APIRouter

from .configs import router as configs_router
from .meetings import router as meetings_router
from .action_items import router as action_items_router
from .dashboard import router as dashboard_router
from .meeting_map import router as meeting_map_router
from .integrations import router as integrations_router
from .report_configs import router as report_configs_router
from .metrics import router as metrics_router
from .reports import router as reports_router

router = APIRouter()

router.include_router(configs_router)
router.include_router(meetings_router)
router.include_router(action_items_router)
router.include_router(dashboard_router)
router.include_router(meeting_map_router)
router.include_router(integrations_router)
router.include_router(report_configs_router)
router.include_router(metrics_router)
router.include_router(reports_router)

__all__ = ['router']
