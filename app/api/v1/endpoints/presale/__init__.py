# -*- coding: utf-8 -*-
"""
售前管理 API - 模块化结构
"""

from fastapi import APIRouter

from .analytics import router as analytics_router
from .bids import router as bids_router
from .dashboard import router as dashboard_router
from .expenses import router as expenses_router
from .forecast import router as forecast_router
from .proposals import router as proposals_router
from .solution_compare import router as solution_compare_router
from .statistics import router as statistics_router
from .task_management import router as task_management_router
from .templates import router as templates_router
from .tickets import router as tickets_router

router = APIRouter()

router.include_router(
    tickets_router, prefix="/tickets", tags=["presale-tickets"]
)  # 移除/presale前缀
router.include_router(proposals_router)
router.include_router(templates_router)
router.include_router(bids_router, tags=["presale-bids"])  # 移除/presale前缀
router.include_router(statistics_router)
router.include_router(analytics_router)
router.include_router(dashboard_router)
router.include_router(task_management_router)
router.include_router(expenses_router)
router.include_router(solution_compare_router)
router.include_router(forecast_router)

__all__ = ["router"]
