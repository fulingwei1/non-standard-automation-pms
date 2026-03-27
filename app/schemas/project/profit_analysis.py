# -*- coding: utf-8 -*-
"""
利润分析 Schema
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    type: str = Field(description="建议类型: cost_overrun/budget_pace/labor_warning")
    cost_type: str = Field(description="成本类型")
    suggestion: str = Field(description="建议内容")
    priority: str = Field(description="优先级: high/medium/low")
    current_amount: Optional[float] = None
    potential_saving: Optional[float] = None


class QuoteVarianceSummary(BaseModel):
    """报价偏差摘要"""
    has_quote: bool = False
    overall_variance: float = 0
    overall_variance_pct: float = 0
    top_variances: List[Dict[str, Any]] = Field(default_factory=list)


class ProfitAnalysisResponse(BaseModel):
    """综合利润分析响应"""
    project_id: int
    current_margin: float = Field(description="当前毛利（元）")
    current_margin_rate: float = Field(description="当前毛利率（%）")
    forecast_margin: float = Field(description="预计毛利（元）")
    forecast_margin_rate: float = Field(description="预计毛利率（%）")
    target_margin_rate: float = Field(description="目标毛利率（%）")
    margin_gap: float = Field(description="当前毛利率与目标差距（百分点）")
    health: str = Field(description="健康度: healthy/warning/critical")
    contract_amount: float = 0
    actual_cost: float = 0
    remaining_cost: float = 0
    forecast_total_cost: float = 0
    optimization_suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    quote_variance: QuoteVarianceSummary = Field(default_factory=QuoteVarianceSummary)


class MarginAnalysisResponse(BaseModel):
    """毛利率分析响应"""
    project_id: int
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    contract_amount: float = 0
    budget_amount: float = 0
    actual_cost: float = 0
    remaining_cost: float = 0
    forecast_total_cost: float = 0
    current_margin: float = 0
    current_margin_rate: float = 0
    forecast_margin: float = 0
    forecast_margin_rate: float = 0
    target_margin_rate: float = 25.0
    margin_gap: float = 0
    forecast_gap: float = 0
    health: str = "healthy"


class HighProfitPatternsResponse(BaseModel):
    """高利润特征分析响应"""
    total_projects_analyzed: int = 0
    high_profit_count: int = 0
    avg_margin_rate: float = 0
    high_profit_threshold: float = 30.0
    high_profit_projects: List[Dict[str, Any]] = Field(default_factory=list)
    patterns: Dict[str, Any] = Field(default_factory=dict)


class LowProfitRootCauseResponse(BaseModel):
    """低利润根因分析响应"""
    total_low_profit: int = 0
    low_profit_threshold: float = 10.0
    low_profit_projects: List[Dict[str, Any]] = Field(default_factory=list)
    warning_signals: List[str] = Field(default_factory=list)
    improvements: List[Dict[str, str]] = Field(default_factory=list)
