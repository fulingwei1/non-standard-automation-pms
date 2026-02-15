# -*- coding: utf-8 -*-
"""
产能分析模块 - API路由聚合
"""

from fastapi import APIRouter

from . import (
    analysis,
    calculation,
    comparison,
    dashboard,
    forecast,
    oee,
    report,
    trend,
    worker_efficiency,
)

router = APIRouter()

# 注册子路由
router.include_router(oee.router, tags=["产能分析-OEE"])
router.include_router(worker_efficiency.router, tags=["产能分析-工人效率"])
router.include_router(analysis.router, tags=["产能分析-分析"])
router.include_router(forecast.router, tags=["产能分析-预测"])
router.include_router(comparison.router, tags=["产能分析-对比"])
router.include_router(trend.router, tags=["产能分析-趋势"])
router.include_router(calculation.router, tags=["产能分析-计算"])
router.include_router(dashboard.router, tags=["产能分析-看板"])
router.include_router(report.router, tags=["产能分析-报告"])

__all__ = ['router']
