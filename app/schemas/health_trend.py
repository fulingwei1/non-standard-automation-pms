# -*- coding: utf-8 -*-
"""
健康度可视化 Schema
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── 健康度趋势 ────────────────────────────────────────────

class HealthTrendPeriod(BaseModel):
    start: str
    end: str
    days: int


class AlertEvent(BaseModel):
    date: Optional[str] = None
    level: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None


class HealthTrendResponse(BaseModel):
    """健康度趋势响应 — health_trend{dates, scores, dimensions, events}"""

    project_id: int
    project_name: str
    period: HealthTrendPeriod
    dates: List[str] = Field(description="日期序列 (ISO 格式)")
    scores: List[int] = Field(description="综合健康度得分序列")
    dimensions: Dict[str, List[int]] = Field(
        description="各维度得分: schedule / cost / resource / quality"
    )
    events: List[AlertEvent] = Field(description="预警事件标记")


# ── 风险因素拆解 ──────────────────────────────────────────

class DimensionDetail(BaseModel):
    key: str
    label: str
    weight: float
    score: int
    weighted_score: float


class Simulation(BaseModel):
    dimension: str
    label: str
    current_score: int
    target_score: int
    current_overall: float
    simulated_overall: float
    improvement: float


class RiskBreakdownResponse(BaseModel):
    project_id: int
    overall_score: float
    current_health: str
    dimensions: List[DimensionDetail]
    weak_factors: List[DimensionDetail]
    simulations: List[Simulation]


# ── 改进建议 ──────────────────────────────────────────────

class Suggestion(BaseModel):
    priority: int
    dimension: str
    dimension_label: str
    current_score: int = 0
    title: str
    description: str
    impact: str = Field(description="high / medium / low")
    effort: str = Field(description="high / medium / low")
    category: str


class SuccessCase(BaseModel):
    project_id: int
    project_name: str
    from_health: str
    to_health: str
    recovered_at: Optional[str] = None
    note: Optional[str] = None


class ImprovementResponse(BaseModel):
    project_id: int
    overall_score: float
    suggestions: List[Suggestion]
    success_cases: List[SuccessCase]
