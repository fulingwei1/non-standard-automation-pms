# -*- coding: utf-8 -*-
"""
同比报告 API 专用 Schema（与 comparison_service.generate_yoy_report 返回结构一致）
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class KPIComparisonItem(BaseModel):
    """KPI 对比项（同比报告用）"""
    kpi_code: str
    kpi_name: str
    current_target: Optional[Decimal] = None
    previous_target: Optional[Decimal] = None
    target_change: Optional[Decimal] = None
    current_completion_rate: Optional[float] = None
    previous_completion_rate: Optional[float] = None
    completion_rate_change: Optional[float] = None
    is_new: bool = False


class CSFComparisonItem(BaseModel):
    """CSF 对比项（同比报告用）"""
    csf_code: str
    csf_name: str
    current_score: Optional[int] = None
    previous_score: Optional[int] = None
    score_change: Optional[float] = None
    is_new: bool = False
    kpi_comparisons: List[KPIComparisonItem] = []


class DimensionComparisonDetail(BaseModel):
    """维度对比详情（同比报告用）"""
    dimension: str
    dimension_name: str
    current_score: Optional[int] = None
    previous_score: Optional[int] = None
    score_change: Optional[float] = None
    csf_comparisons: List[CSFComparisonItem] = []


class YoYReportResponse(BaseModel):
    """同比报告响应（GET /strategy/comparisons/yoy-report）"""
    current_year: int
    previous_year: int
    current_strategy_id: Optional[int] = None
    previous_strategy_id: Optional[int] = None
    dimensions: List[DimensionComparisonDetail] = []
    overall_health_change: Optional[float] = None
    generated_at: date
