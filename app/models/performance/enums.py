# -*- coding: utf-8 -*-
"""
绩效模型 - 枚举定义
"""
from enum import Enum


class PerformancePeriodTypeEnum(str, Enum):
    """考核周期类型"""
    WEEKLY = 'WEEKLY'        # 周
    MONTHLY = 'MONTHLY'      # 月
    QUARTERLY = 'QUARTERLY'  # 季度
    YEARLY = 'YEARLY'        # 年度


class PerformanceLevelEnum(str, Enum):
    """绩效等级"""
    EXCELLENT = 'EXCELLENT'              # 优秀 (A)
    GOOD = 'GOOD'                        # 良好 (B)
    QUALIFIED = 'QUALIFIED'              # 合格 (C)
    NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT'  # 待改进 (D)
    # 兼容物料模块历史值
    AVERAGE = 'AVERAGE'
    POOR = 'POOR'


class IndicatorTypeEnum(str, Enum):
    """指标类型"""
    WORKLOAD = 'WORKLOAD'        # 工作量指标
    TASK = 'TASK'                # 任务指标
    QUALITY = 'QUALITY'          # 质量指标
    COLLABORATION = 'COLLABORATION'  # 协作指标
    GROWTH = 'GROWTH'            # 成长指标


class PerformanceStatusEnum(str, Enum):
    """绩效状态"""
    PENDING = 'PENDING'          # 待计算
    CALCULATED = 'CALCULATED'    # 已计算
    REVIEWING = 'REVIEWING'      # 评审中
    CONFIRMED = 'CONFIRMED'      # 已确认
    APPEALING = 'APPEALING'      # 申诉中
    FINALIZED = 'FINALIZED'      # 已定稿


class MonthlySummaryStatusEnum(str, Enum):
    """月度总结状态"""
    DRAFT = 'DRAFT'              # 草稿
    SUBMITTED = 'SUBMITTED'      # 已提交
    EVALUATING = 'EVALUATING'    # 评价中
    COMPLETED = 'COMPLETED'      # 已完成


class EvaluatorTypeEnum(str, Enum):
    """评价人类型"""
    DEPT_MANAGER = 'DEPT_MANAGER'      # 部门经理
    PROJECT_MANAGER = 'PROJECT_MANAGER'  # 项目经理


class EvaluationStatusEnum(str, Enum):
    """评价状态"""
    PENDING = 'PENDING'      # 待评价
    COMPLETED = 'COMPLETED'  # 已完成
