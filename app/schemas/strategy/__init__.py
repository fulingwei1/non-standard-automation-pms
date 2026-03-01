# -*- coding: utf-8 -*-
"""
战略管理 Schema 模块

此模块提供 BEM 战略管理相关的所有 Pydantic Schema 类。
"""

# Strategy - 战略主表
from .strategy import (
    StrategyCreate,
    StrategyDetailResponse,
    StrategyMapCSF,
    StrategyMapDimension,
    StrategyMapResponse,
    StrategyPublishRequest,
    StrategyResponse,
    StrategyUpdate,
)

# CSF - 关键成功要素
from .csf import (
    CSFBatchCreateRequest,
    CSFByDimensionItem,
    CSFByDimensionResponse,
    CSFCreate,
    CSFDetailResponse,
    CSFResponse,
    CSFUpdate,
)

# KPI - 关键绩效指标
from .kpi import (
    KPICollectRequest,
    KPICollectResponse,
    KPICreate,
    KPIDataSourceCreate,
    KPIDataSourceResponse,
    KPIDetailResponse,
    KPIHistoryResponse,
    KPIResponse,
    KPITrendData,
    KPITrendResponse,
    KPIUpdate,
    KPIValueUpdate,
    KPIWithHistoryResponse,
)

# AnnualKeyWork - 年度重点工作
from .annual_work import (
    AnnualKeyWorkCreate,
    AnnualKeyWorkDetailResponse,
    AnnualKeyWorkProgressUpdate,
    AnnualKeyWorkResponse,
    AnnualKeyWorkUpdate,
    LinkProjectRequest,
    ProjectLinkItem,
    UnlinkProjectRequest,
)

# Decomposition - 目标分解
from .decomposition import (
    DecompositionTreeNode,
    DecompositionTreeResponse,
    DepartmentObjectiveCreate,
    DepartmentObjectiveDetailResponse,
    DepartmentObjectiveResponse,
    DepartmentObjectiveUpdate,
    PersonalKPIBatchCreate,
    PersonalKPICreate,
    PersonalKPIManagerRatingRequest,
    PersonalKPIResponse,
    PersonalKPISelfRatingRequest,
    PersonalKPIUpdate,
    TraceToStrategyResponse,
)

# Review - 战略审视
from .review import (
    CalendarMonthResponse,
    CalendarYearResponse,
    DimensionHealthDetail,
    HealthScoreResponse,
    RoutineManagementCycleItem,
    RoutineManagementCycleResponse,
    StrategyCalendarEventCreate,
    StrategyCalendarEventResponse,
    StrategyCalendarEventUpdate,
    StrategyReviewCreate,
    StrategyReviewResponse,
    StrategyReviewUpdate,
)

# Dashboard & Comparison - 仪表板与同比分析
from .dashboard import (
    CSFComparisonItem,
    DimensionComparisonDetail,
    ExecutionStatusItem,
    ExecutionStatusResponse,
    KPIComparisonItem,
    MyStrategyItem,
    MyStrategyResponse,
    MyStrategyDashboardResponse,
    StrategyComparisonCreate,
    StrategyComparisonResponse,
    StrategyOverviewResponse,
    YoYReportResponse,
)

__all__ = [
    # Strategy
    "StrategyCreate",
    "StrategyUpdate",
    "StrategyResponse",
    "StrategyDetailResponse",
    "StrategyPublishRequest",
    "StrategyMapCSF",
    "StrategyMapDimension",
    "StrategyMapResponse",
    # CSF
    "CSFCreate",
    "CSFUpdate",
    "CSFResponse",
    "CSFDetailResponse",
    "CSFByDimensionItem",
    "CSFByDimensionResponse",
    "CSFBatchCreateRequest",
    # KPI
    "KPICreate",
    "KPIUpdate",
    "KPIResponse",
    "KPIDetailResponse",
    "KPIValueUpdate",
    "KPICollectRequest",
    "KPICollectResponse",
    "KPIHistoryResponse",
    "KPIWithHistoryResponse",
    "KPITrendData",
    "KPITrendResponse",
    "KPIDataSourceCreate",
    "KPIDataSourceResponse",
    # AnnualKeyWork
    "AnnualKeyWorkCreate",
    "AnnualKeyWorkUpdate",
    "AnnualKeyWorkResponse",
    "AnnualKeyWorkDetailResponse",
    "AnnualKeyWorkProgressUpdate",
    "ProjectLinkItem",
    "LinkProjectRequest",
    "UnlinkProjectRequest",
    # Decomposition
    "DepartmentObjectiveCreate",
    "DepartmentObjectiveUpdate",
    "DepartmentObjectiveResponse",
    "DepartmentObjectiveDetailResponse",
    "PersonalKPICreate",
    "PersonalKPIUpdate",
    "PersonalKPIResponse",
    "PersonalKPISelfRatingRequest",
    "PersonalKPIManagerRatingRequest",
    "PersonalKPIBatchCreate",
    "DecompositionTreeNode",
    "DecompositionTreeResponse",
    "TraceToStrategyResponse",
    # Review
    "StrategyReviewCreate",
    "StrategyReviewUpdate",
    "StrategyReviewResponse",
    "HealthScoreResponse",
    "DimensionHealthDetail",
    "StrategyCalendarEventCreate",
    "StrategyCalendarEventUpdate",
    "StrategyCalendarEventResponse",
    "CalendarMonthResponse",
    "CalendarYearResponse",
    "RoutineManagementCycleItem",
    "RoutineManagementCycleResponse",
    # Dashboard
    "StrategyOverviewResponse",
    "MyStrategyItem",
    "MyStrategyResponse",
    "MyStrategyDashboardResponse",
    "ExecutionStatusItem",
    "ExecutionStatusResponse",
    # Comparison
    "StrategyComparisonCreate",
    "StrategyComparisonResponse",
    "DimensionComparisonDetail",
    "CSFComparisonItem",
    "KPIComparisonItem",
    "YoYReportResponse",
]
