# -*- coding: utf-8 -*-
"""
SLA管理模块

拆分自原 sla.py (574行)，按功能域分为：
- policies: SLA策略管理
- monitors: SLA监控记录
- statistics: SLA统计分析
"""

from fastapi import APIRouter

from .monitors import router as monitors_router
from .policies import router as policies_router
from .statistics import router as statistics_router

router = APIRouter()

# SLA策略管理
router.include_router(policies_router, tags=["SLA策略"])

# SLA监控记录
router.include_router(monitors_router, tags=["SLA监控"])

# SLA统计分析
router.include_router(statistics_router, tags=["SLA统计"])
