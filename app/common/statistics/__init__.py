# -*- coding: utf-8 -*-
"""
统一统计服务模块
提供统一的统计基类，减少重复代码
"""

from app.common.statistics.base import BaseStatisticsService
from app.common.statistics.aggregator import StatisticsAggregator
from app.common.statistics.dashboard import BaseDashboardService

__all__ = [
    "BaseStatisticsService",
    "StatisticsAggregator",
    "BaseDashboardService",
]
