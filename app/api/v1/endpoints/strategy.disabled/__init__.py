# -*- coding: utf-8 -*-
"""
战略管理 API 端点模块

聚合所有战略管理相关的 API 路由
"""

from fastapi import APIRouter

from .annual_work import router as annual_work_router
from .comparison import router as comparison_router
from .csf import router as csf_router
from .dashboard import router as dashboard_router
from .decomposition import router as decomposition_router
from .kpi import router as kpi_router
from .review import router as review_router
from .strategy import router as strategy_router

router = APIRouter()

# 战略主路由
router.include_router(strategy_router, prefix="/strategies", tags=["战略管理 - 战略"])

# CSF 路由
router.include_router(csf_router, prefix="/csfs", tags=["战略管理 - CSF"])

# KPI 路由
router.include_router(kpi_router, prefix="/kpis", tags=["战略管理 - KPI"])

# 年度重点工作路由
router.include_router(annual_work_router, prefix="/annual-works", tags=["战略管理 - 年度重点工作"])

# 目标分解路由
router.include_router(decomposition_router, prefix="/decomposition", tags=["战略管理 - 目标分解"])

# 战略审视路由
router.include_router(review_router, prefix="", tags=["战略管理 - 审视与日历"])

# 同比分析路由
router.include_router(comparison_router, prefix="/comparisons", tags=["战略管理 - 同比分析"])

# 仪表板路由
router.include_router(dashboard_router, prefix="/dashboard", tags=["战略管理 - 仪表板"])
