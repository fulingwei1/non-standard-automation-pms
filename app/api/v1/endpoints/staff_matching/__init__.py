# -*- coding: utf-8 -*-
"""
AI驱动人员智能匹配 API - 模块化结构
"""

from fastapi import APIRouter

from .dashboard import router as dashboard_router
from .evaluations import router as evaluations_router
from .matching import router as matching_router
from .performance import router as performance_router
from .profiles import router as profiles_router
from .staffing_needs import router as staffing_needs_router
from .tags import router as tags_router

router = APIRouter()

router.include_router(tags_router, prefix="/tags")
router.include_router(evaluations_router, prefix="/evaluations")
router.include_router(profiles_router, prefix="/profiles")
router.include_router(performance_router, prefix="/performance")
router.include_router(staffing_needs_router, prefix="/staffing-needs")
router.include_router(matching_router, prefix="/matching")
router.include_router(dashboard_router)

__all__ = ["router"]
