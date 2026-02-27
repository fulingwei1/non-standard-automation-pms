# -*- coding: utf-8 -*-
"""
统计服务模块

提供同步统计服务基类和聚合接口。

已有的异步基类在 app.common.statistics.base.BaseStatisticsService，
本模块提供同步版本，供现有的同步统计服务（如 issue_statistics_service,
payment_statistics_service 等）逐步迁移使用。

Usage:
    from app.services.statistics import SyncStatisticsService

    class IssueStatistics(SyncStatisticsService):
        model = Issue
        default_status_field = "status"
        default_exclude_statuses = ["DELETED"]
"""

from app.services.statistics.base import (
    AggregationServiceProtocol,
    SyncStatisticsService,
)

__all__ = [
    "SyncStatisticsService",
    "AggregationServiceProtocol",
]
