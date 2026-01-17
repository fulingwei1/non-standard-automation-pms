# -*- coding: utf-8 -*-
"""
短缺预警 API - 模块化结构
"""

from fastapi import APIRouter

from .alerts_crud import router as alerts_router
from .arrivals import router as arrivals_router
from .reports import router as reports_router
from .statistics import router as statistics_router
from .substitutions import router as substitutions_router
from .transfers import router as transfers_router

router = APIRouter()

router.include_router(alerts_router)
router.include_router(statistics_router)
router.include_router(reports_router)
router.include_router(arrivals_router)
router.include_router(substitutions_router)
router.include_router(transfers_router)

__all__ = ['router']
