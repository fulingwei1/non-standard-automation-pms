# -*- coding: utf-8 -*-
"""
仪表盘路由模块
"""

from fastapi import APIRouter

from .cost_dashboard import router as cost_dashboard_router

router = APIRouter()

router.include_router(
    cost_dashboard_router,
    prefix="/cost",
    tags=["dashboard-cost"]
)
