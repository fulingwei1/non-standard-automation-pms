# -*- coding: utf-8 -*-
"""
预算执行预警 Schema

输出格式：budget_status{execution_rate, forecast_variance, alert_level}
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class CostBreakdown(BaseModel):
    """成本分解"""

    actual_cost: Decimal = Field(description="已发生成本")
    committed_cost: Decimal = Field(description="已承诺成本（PO已下未到货）")
    forecast_remaining: Decimal = Field(description="预计剩余成本")
    total_forecast: Decimal = Field(description="预计总成本 = 已发生 + 已承诺 + 预计剩余")


class ExecutionRates(BaseModel):
    """执行率指标"""

    actual_rate: Decimal = Field(description="已发生成本执行率 (%)")
    committed_rate: Decimal = Field(description="(已发生+已承诺) / 预算 (%)")
    forecast_rate: Decimal = Field(description="预计总成本 / 预算 (%)")


class CostTrendPoint(BaseModel):
    """成本趋势数据点"""

    month: str = Field(description="月份 (YYYY-MM)")
    actual_cost: Decimal = Field(description="当月实际成本")
    cumulative_cost: Decimal = Field(description="累计成本")


class CostTrendPrediction(BaseModel):
    """成本趋势预测"""

    monthly_burn_rate: Decimal = Field(description="月均消耗速率")
    estimated_completion_cost: Decimal = Field(description="预测完工成本")
    months_to_budget_exhaust: Optional[Decimal] = Field(
        None, description="预算耗尽剩余月数（None=不会超支）"
    )
    historical_deviation_pct: Optional[Decimal] = Field(
        None, description="相比历史类似项目的偏差率 (%)"
    )
    trend_direction: str = Field(description="趋势方向: IMPROVING/STABLE/WORSENING")
    confidence: Decimal = Field(description="预测置信度 (0-100)")


class BudgetAlertInfo(BaseModel):
    """预警信息"""

    alert_level: str = Field(description="预警级别: GREEN/YELLOW/ORANGE/RED")
    alert_reasons: List[str] = Field(description="预警原因列表")
    recommended_actions: List[str] = Field(description="建议措施")


class BudgetStatusResponse(BaseModel):
    """预算执行状态 — 主输出格式

    budget_status{execution_rate, forecast_variance, alert_level}
    """

    project_id: int
    project_code: str
    project_name: str
    budget_amount: Decimal = Field(description="预算总额")

    # 核心指标
    execution_rate: Decimal = Field(description="已发生成本执行率 (%)")
    forecast_variance: Decimal = Field(description="预计总成本偏差 = (预计总成本 - 预算) / 预算 (%)")
    alert_level: str = Field(description="预警级别: GREEN/YELLOW/ORANGE/RED")

    # 详细分解
    cost_breakdown: CostBreakdown
    execution_rates: ExecutionRates
    alert_info: BudgetAlertInfo

    # 趋势预测（可选，计算量大时可跳过）
    trend_prediction: Optional[CostTrendPrediction] = None
    trend_data: Optional[List[CostTrendPoint]] = None

    # 元信息
    calculated_at: datetime = Field(default_factory=datetime.now)


class BudgetAlertConfig(BaseModel):
    """预警阈值配置"""

    yellow_threshold: Decimal = Field(default=Decimal("80"), description="黄色预警阈值 (%)")
    orange_threshold: Decimal = Field(default=Decimal("90"), description="橙色预警阈值 (%)")
    red_threshold: Decimal = Field(default=Decimal("100"), description="红色预警阈值 (%)")


class BudgetMonitorRequest(BaseModel):
    """预算监控请求"""

    project_ids: Optional[List[int]] = Field(None, description="项目ID列表（空=所有活跃项目）")
    include_trend: bool = Field(default=False, description="是否包含趋势预测")
    alert_config: Optional[BudgetAlertConfig] = Field(None, description="自定义预警阈值")


class BudgetMonitorSummary(BaseModel):
    """批量监控汇总"""

    total_projects: int
    green_count: int = 0
    yellow_count: int = 0
    orange_count: int = 0
    red_count: int = 0
    projects: List[BudgetStatusResponse] = []
    calculated_at: datetime = Field(default_factory=datetime.now)
