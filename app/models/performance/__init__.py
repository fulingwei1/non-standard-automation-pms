# -*- coding: utf-8 -*-
"""
绩效模型模块

聚合所有绩效管理相关的模型，保持向后兼容
"""
from .appeal_adjustment import PerformanceAdjustmentHistory, PerformanceAppeal
from .contribution_ranking import PerformanceRankingSnapshot, ProjectContribution
from .enums import (
    EvaluationStatusEnum,
    EvaluatorTypeEnum,
    IndicatorTypeEnum,
    MonthlySummaryStatusEnum,
    PerformanceLevelEnum,
    PerformancePeriodTypeEnum,
    PerformanceStatusEnum,
)
from .monthly_system import (
    EvaluationWeightConfig,
    MonthlyWorkSummary,
    PerformanceEvaluationRecord,
)
from .period_indicator import PerformanceIndicator, PerformancePeriod
from .result_evaluation import PerformanceEvaluation, PerformanceResult

__all__ = [
    # Enums
    "PerformancePeriodTypeEnum",
    "PerformanceLevelEnum",
    "IndicatorTypeEnum",
    "PerformanceStatusEnum",
    "MonthlySummaryStatusEnum",
    "EvaluatorTypeEnum",
    "EvaluationStatusEnum",
    # Period and Indicator
    "PerformancePeriod",
    "PerformanceIndicator",
    # Result and Evaluation
    "PerformanceResult",
    "PerformanceEvaluation",
    # Appeal and Adjustment
    "PerformanceAppeal",
    "PerformanceAdjustmentHistory",
    # Contribution and Ranking
    "ProjectContribution",
    "PerformanceRankingSnapshot",
    # Monthly System
    "MonthlyWorkSummary",
    "PerformanceEvaluationRecord",
    "EvaluationWeightConfig",
]
