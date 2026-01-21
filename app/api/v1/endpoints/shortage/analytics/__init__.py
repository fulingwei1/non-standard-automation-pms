"""
缺料管理 - Analytics 层（统计报表）

职责：分析问题
- 统计概览、原因分析（statistics）
- 看板、日报、趋势（dashboard）
"""
from fastapi import APIRouter

from . import statistics, dashboard

router = APIRouter()

router.include_router(statistics.router, tags=["缺料-统计报表"])
router.include_router(dashboard.router, tags=["缺料-统计报表"])
