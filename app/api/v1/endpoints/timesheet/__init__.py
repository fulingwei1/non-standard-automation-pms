# -*- coding: utf-8 -*-
"""
工时管理模块 API

提供工时记录管理和审批工作流功能。
"""

from fastapi import APIRouter

from .records import router as records_router
from .pending import router as pending_router
from .weekly import router as weekly_router
from .monthly import router as monthly_router
from .statistics import router as statistics_router
from .reports import router as reports_router
from .reports_unified import router as reports_unified_router
from .workflow import router as workflow_router
from .analytics import router as analytics_router

router = APIRouter()

# 注册所有子路由
router.include_router(records_router)
router.include_router(pending_router)
router.include_router(weekly_router)
router.include_router(monthly_router)
router.include_router(statistics_router)
router.include_router(reports_router)
router.include_router(reports_unified_router)
router.include_router(workflow_router)
router.include_router(analytics_router, prefix="/analytics", tags=["工时分析与预测"])

__all__ = ["router"]
