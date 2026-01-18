# -*- coding: utf-8 -*-
"""
缺料统计 API endpoints - 路由聚合

已拆分为模块化结构：
- statistics_helpers.py: 辅助函数（编号生成、报表构建）
- statistics_dashboard.py: 缺料看板
- statistics_supplier.py: 供应商交期分析
- statistics_daily_report.py: 缺料日报（get, latest, by-date）
- statistics_analysis.py: 缺料原因分析和齐套率统计
"""

from fastapi import APIRouter

from . import (
    statistics_analysis,
    statistics_dashboard,
    statistics_daily_report,
    statistics_supplier,
)

router = APIRouter(
    prefix="/shortage",
    tags=["statistics"]
)

# 聚合所有子路由
router.include_router(statistics_dashboard.router)
router.include_router(statistics_supplier.router)
router.include_router(statistics_daily_report.router)
router.include_router(statistics_analysis.router)
