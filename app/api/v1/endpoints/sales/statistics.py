# -*- coding: utf-8 -*-
"""
销售统计与报表 API endpoints - 路由聚合

已拆分为模块化结构：
- statistics_core.py: 核心统计（funnel, opportunities-by-stage, summary）
- statistics_prediction.py: 预测相关（revenue-forecast, prediction, prediction/accuracy）
- statistics_quotes.py: 报价统计（quote-stats）
- statistics_reports.py: 报表（sales-funnel, win-loss, sales-performance, customer-contribution, o2c-pipeline）
"""

from fastapi import APIRouter

from . import statistics_core, statistics_prediction, statistics_quotes, statistics_reports

router = APIRouter()

# 聚合所有子路由
router.include_router(statistics_core.router)
router.include_router(statistics_prediction.router)
router.include_router(statistics_quotes.router)
router.include_router(statistics_reports.router)
