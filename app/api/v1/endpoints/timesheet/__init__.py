# -*- coding: utf-8 -*-
"""
工时管理 API - 模块化结构
"""

from fastapi import APIRouter

from .records import router as records_router
from .approval import router as approval_router
from .weekly import router as weekly_router
from .monthly import router as monthly_router
from .pending import router as pending_router
from .statistics import router as statistics_router
from .reports import router as reports_router

router = APIRouter()

router.include_router(records_router)
router.include_router(approval_router)
router.include_router(weekly_router)
router.include_router(monthly_router)
router.include_router(pending_router)
router.include_router(statistics_router)
router.include_router(reports_router)

__all__ = ['router']
