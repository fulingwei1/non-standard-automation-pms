# -*- coding: utf-8 -*-
"""
统一统计服务模块
提供统一的统计基类，减少重复代码
"""

from app.common.statistics.aggregator import StatisticsAggregator
from app.common.statistics.base import BaseStatisticsService
from app.common.statistics.dashboard import BaseDashboardService
from app.common.statistics.helpers import (
    calculate_trend,
    create_stat_card,
    create_stats_response,
    format_currency,
    format_hours,
    format_percentage,
)

__all__ = [
    "BaseStatisticsService",
    "StatisticsAggregator",
    "BaseDashboardService",
    "format_currency",
    "format_hours",
    "format_percentage",
    "create_stat_card",
    "create_stats_response",
    "calculate_trend",
]
