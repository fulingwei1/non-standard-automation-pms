# -*- coding: utf-8 -*-
"""
工时管理 API - 模块化结构
"""

from fastapi import APIRouter

from .approval import router as approval_router
from .monthly import router as monthly_router
from .pending import router as pending_router
from .records import router as records_router
from .reports import router as reports_router
from .reports_unified import router as reports_unified_router
from .statistics import router as statistics_router
from .weekly import router as weekly_router

router = APIRouter()

router.include_router(records_router)
router.include_router(approval_router)
router.include_router(weekly_router)
router.include_router(monthly_router)
router.include_router(pending_router)
router.include_router(statistics_router)
router.include_router(reports_router)
router.include_router(reports_unified_router)  # 统一报表框架版本

__all__ = ["router"]
