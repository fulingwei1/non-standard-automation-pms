# -*- coding: utf-8 -*-
"""
战略管理 Schema - 仪表板与同比分析
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


# ============================================
# Dashboard - 仪表板
# ============================================

class StrategyOverviewResponse(BaseModel):
    """战略总览响应"""
    strategy_id: int
    strategy_code: Optional[str] = None
    strategy_name: str
    year: int
    status: str
    vision: Optional[str] = None
    slogan: Optional[str] = None

    # 健康度
    overall_health_score: int = 0
    financial_health: int = 0
    customer_health: int = 0
    internal_health: int = 0
    learning_health: int = 0

    # 统计
    csf_count: int = 0
    kpi_count: int = 0
    kpi_completion_rate: float = 0
    annual_work_count: int = 0
    annual_work_completion_rate: float = 0

    # 趋势
    health_trend: str = "STABLE"  # UP/DOWN/STABLE
    last_review_date: Optional[date] = None
    next_review_date: Optional[date] = None

    class Config:
        from_attributes = True


class MyStrategyItem(BaseModel):
    """我的战略关联项"""
    type: str  # KPI / ANNUAL_WORK / DEPT_OBJECTIVE
    id: int
    name: str
    target_value: Optional[float] = None
    current_value: Optional[float] = None
    completion_rate: Optional[float] = None
    weight: float = 0
    status: Optional[str] = None
    due_date: Optional[date] = None
    source_path: List[str] = []  # 追溯路径


class MyStrategyResponse(BaseModel):
    """我的战略关联响应"""
    employee_id: int
    employee_name: str
    department_name: Optional[str] = None
    year: int

    # 个人 KPI 汇总
    personal_kpi_count: int = 0
    personal_kpi_avg_completion: float = 0
    personal_kpi_weighted_score: float = 0

    # 关联项列表
    kpis: List[MyStrategyItem] = []
    annual_works: List[MyStrategyItem] = []

    # 战略穿透路径
    strategy_path: str = ""  # e.g., "公司战略 → 研发部目标 → 我的 KPI"

    class Config:
        from_attributes = True


class ExecutionStatusItem(BaseModel):
    """执行状态项"""
    dimension: str
    dimension_name: str
    csf_count: int
    kpi_count: int
    kpi_on_track: int
    kpi_at_risk: int
    kpi_off_track: int
    annual_work_count: int
    annual_work_completed: int
    annual_work_in_progress: int
    annual_work_delayed: int
    health_score: int
    health_level: str


class ExecutionStatusResponse(BaseModel):
    """执行状态看板响应"""
    strategy_id: int
    strategy_name: str
    year: int
    as_of_date: date
    dimensions: List[ExecutionStatusItem] = []
    overall_kpi_on_track_rate: float = 0
    overall_work_completion_rate: float = 0
    alerts: List[str] = []  # 预警信息

    class Config:
        from_attributes = True


# ============================================
# Comparison - 同比分析
# ============================================

class StrategyComparisonCreate(BaseModel):
    """创建战略对比"""
    current_strategy_id: int = Field(description="当前战略ID")
    previous_strategy_id: Optional[int] = Field(default=None, description="对比战略ID")
    current_year: int = Field(description="当前年份")
    previous_year: Optional[int] = Field(default=None, description="对比年份")


class StrategyComparisonResponse(TimestampSchema):
    """战略对比响应"""
    id: int
    current_strategy_id: int
    previous_strategy_id: Optional[int] = None
    current_year: int
    previous_year: Optional[int] = None
    generated_date: date
    generated_by: Optional[int] = None

    # 总体健康度对比
    current_health_score: Optional[int] = None
    previous_health_score: Optional[int] = None
    health_change: Optional[int] = None

    # 各维度对比
    current_financial_score: Optional[int] = None
    previous_financial_score: Optional[int] = None
    financial_change: Optional[int] = None

    current_customer_score: Optional[int] = None
    previous_customer_score: Optional[int] = None
    customer_change: Optional[int] = None

    current_internal_score: Optional[int] = None
    previous_internal_score: Optional[int] = None
    internal_change: Optional[int] = None

    current_learning_score: Optional[int] = None
    previous_learning_score: Optional[int] = None
    learning_change: Optional[int] = None

    # KPI 完成率对比
    kpi_completion_rate: Optional[Decimal] = None
    previous_kpi_completion_rate: Optional[Decimal] = None
    kpi_completion_change: Optional[Decimal] = None

    # 重点工作完成率对比
    work_completion_rate: Optional[Decimal] = None
    previous_work_completion_rate: Optional[Decimal] = None
    work_completion_change: Optional[Decimal] = None

    # 分析结论
    summary: Optional[str] = None
    highlights: Optional[List[str]] = None
    improvements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None

    is_active: bool = True

    # 扩展字段
    generator_name: Optional[str] = None
    current_strategy_name: Optional[str] = None
    previous_strategy_name: Optional[str] = None


class DimensionComparisonDetail(BaseModel):
    """维度对比详情"""
    dimension: str
    dimension_name: str
    current_score: int
    previous_score: Optional[int] = None
    change: Optional[int] = None
    change_trend: str  # UP/DOWN/STABLE
    current_csf_count: int
    previous_csf_count: Optional[int] = None
    current_kpi_completion_rate: float
    previous_kpi_completion_rate: Optional[float] = None
    key_changes: List[str] = []


class CSFComparisonItem(BaseModel):
    """CSF 对比项"""
    csf_id: int
    csf_code: str
    csf_name: str
    dimension: str
    current_health_score: Optional[int] = None
    previous_health_score: Optional[int] = None
    change: Optional[int] = None
    current_kpi_count: int
    previous_kpi_count: Optional[int] = None
    new_in_current_year: bool = False
    removed_in_current_year: bool = False


class KPIComparisonItem(BaseModel):
    """KPI 对比项"""
    kpi_id: int
    kpi_code: str
    kpi_name: str
    csf_name: str
    current_target: Optional[float] = None
    previous_target: Optional[float] = None
    target_change: Optional[float] = None
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    value_change: Optional[float] = None
    current_completion_rate: Optional[float] = None
    previous_completion_rate: Optional[float] = None
    completion_change: Optional[float] = None


class YoYReportResponse(BaseModel):
    """同比报告响应"""
    current_year: int
    previous_year: int
    generated_date: date

    # 总体对比
    overall_health_current: int
    overall_health_previous: int
    overall_change: int
    overall_trend: str

    # 维度对比
    dimension_comparisons: List[DimensionComparisonDetail] = []

    # CSF 对比
    csf_comparisons: List[CSFComparisonItem] = []
    new_csfs: int = 0
    removed_csfs: int = 0

    # KPI 对比（Top N）
    top_improved_kpis: List[KPIComparisonItem] = []
    top_declined_kpis: List[KPIComparisonItem] = []

    # 重点工作对比
    work_completion_current: float
    work_completion_previous: float
    work_completion_change: float

    # 分析结论
    executive_summary: str = ""
    key_achievements: List[str] = []
    areas_for_improvement: List[str] = []
    strategic_recommendations: List[str] = []

    class Config:
        from_attributes = True
