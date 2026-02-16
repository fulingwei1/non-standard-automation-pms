# -*- coding: utf-8 -*-
"""
智能缺料预警系统 - Schemas

Team 3: 智能缺料预警系统
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ==================== 缺料预警 ====================

class ShortageAlertBase(BaseModel):
    """缺料预警基础"""
    project_id: int = Field(description="项目ID")
    material_id: int = Field(description="物料ID")
    required_qty: Decimal = Field(gt=0, description="需求数量")
    required_date: Optional[date] = Field(None, description="需求日期")
    remark: Optional[str] = None


class ShortageAlertCreate(ShortageAlertBase):
    """创建缺料预警"""
    work_order_id: Optional[int] = None
    alert_level: Optional[str] = Field('WARNING', description="预警级别")


class ShortageAlertResponse(BaseModel):
    """缺料预警响应"""
    id: int
    alert_no: str
    project_id: int
    material_id: int
    material_code: str
    material_name: str
    material_spec: Optional[str]
    required_qty: Decimal
    available_qty: Decimal
    shortage_qty: Decimal
    in_transit_qty: Decimal
    alert_level: str
    alert_date: date
    required_date: Optional[date]
    expected_arrival_date: Optional[date]
    days_to_shortage: int
    impact_projects: Optional[List[Dict]]
    estimated_delay_days: int
    estimated_cost_impact: Decimal
    is_critical_path: bool
    risk_score: Decimal
    status: str
    auto_handled: bool
    handling_plan_id: Optional[int]
    detected_at: datetime
    notified_at: Optional[datetime]
    handled_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolution_type: Optional[str]
    resolution_note: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShortageAlertListResponse(BaseModel):
    """缺料预警列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ShortageAlertResponse]


class ScanShortageRequest(BaseModel):
    """扫描缺料请求"""
    project_id: Optional[int] = Field(None, description="项目ID，为空则全局扫描")
    material_id: Optional[int] = Field(None, description="物料ID，为空则扫描全部物料")
    days_ahead: int = Field(30, description="提前天数", ge=1, le=180)


class ScanShortageResponse(BaseModel):
    """扫描缺料响应"""
    scanned_at: datetime
    alerts_generated: int
    alerts: List[ShortageAlertResponse]


class ResolveAlertRequest(BaseModel):
    """解决预警请求"""
    resolution_type: str = Field(description="解决方式: PURCHASE/SUBSTITUTE/TRANSFER/RESCHEDULE")
    resolution_note: Optional[str] = None
    actual_cost_impact: Optional[Decimal] = None
    actual_delay_days: Optional[int] = None


# ==================== 处理方案 ====================

class HandlingPlanBase(BaseModel):
    """处理方案基础"""
    solution_type: str = Field(description="方案类型")
    solution_name: str
    solution_description: Optional[str] = None


class HandlingPlanResponse(BaseModel):
    """处理方案响应"""
    id: int
    plan_no: str
    alert_id: int
    solution_type: str
    solution_name: str
    solution_description: Optional[str]
    target_material_id: Optional[int]
    target_supplier_id: Optional[int]
    target_project_id: Optional[int]
    proposed_qty: Optional[Decimal]
    proposed_date: Optional[date]
    estimated_lead_time: Optional[int]
    estimated_cost: Optional[Decimal]
    ai_score: Decimal
    feasibility_score: Decimal
    cost_score: Decimal
    time_score: Decimal
    risk_score: Decimal
    score_weights: Optional[Dict]
    score_explanation: Optional[str]
    advantages: Optional[List[str]]
    disadvantages: Optional[List[str]]
    risks: Optional[List[str]]
    is_recommended: bool
    recommendation_rank: int
    status: str
    approved_at: Optional[datetime]
    executed_at: Optional[datetime]
    completed_at: Optional[datetime]
    execution_result: Optional[Dict]
    actual_cost: Optional[Decimal]
    actual_lead_time: Optional[int]
    effectiveness_rating: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HandlingPlanListResponse(BaseModel):
    """处理方案列表响应"""
    alert_id: int
    total: int
    items: List[HandlingPlanResponse]


# ==================== 需求预测 ====================

class DemandForecastRequest(BaseModel):
    """需求预测请求"""
    material_id: int = Field(description="物料ID")
    forecast_horizon_days: int = Field(30, description="预测周期（天）", ge=1, le=365)
    algorithm: str = Field('EXP_SMOOTHING', description="预测算法")
    historical_days: int = Field(90, description="历史数据周期（天）", ge=7, le=365)
    project_id: Optional[int] = Field(None, description="项目ID（可选）")


class DemandForecastResponse(BaseModel):
    """需求预测响应"""
    id: int
    forecast_no: str
    material_id: int
    project_id: Optional[int]
    forecast_start_date: date
    forecast_end_date: date
    forecast_horizon_days: int
    algorithm: str
    algorithm_params: Optional[Dict]
    forecasted_demand: Decimal
    lower_bound: Optional[Decimal]
    upper_bound: Optional[Decimal]
    confidence_interval: Decimal
    historical_avg: Optional[Decimal]
    historical_std: Optional[Decimal]
    historical_period_days: int
    seasonal_factor: Decimal
    seasonal_pattern: Optional[Dict]
    accuracy_score: Optional[Decimal]
    mae: Optional[Decimal]
    rmse: Optional[Decimal]
    mape: Optional[Decimal]
    actual_demand: Optional[Decimal]
    forecast_error: Optional[Decimal]
    error_percentage: Optional[Decimal]
    status: str
    forecast_date: date
    validated_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ValidateForecastRequest(BaseModel):
    """验证预测请求"""
    actual_demand: Decimal = Field(gt=0, description="实际需求量")


class ValidateForecastResponse(BaseModel):
    """验证预测响应"""
    forecast_id: int
    forecasted_demand: float
    actual_demand: float
    error: float
    error_percentage: float
    accuracy_score: float
    mae: float
    rmse: float
    mape: float
    within_confidence_interval: bool


# ==================== 分析报表 ====================

class ShortageTrendResponse(BaseModel):
    """缺料趋势分析"""
    period_start: date
    period_end: date
    total_alerts: int
    by_level: Dict[str, int]
    by_status: Dict[str, int]
    avg_resolution_hours: float
    total_cost_impact: Decimal
    trend_data: List[Dict[str, Any]]  # 每日趋势数据


class RootCauseAnalysis(BaseModel):
    """根因分析"""
    cause: str
    count: int
    percentage: float
    avg_cost_impact: Decimal
    examples: List[str]  # 示例预警单号


class RootCauseResponse(BaseModel):
    """根因分析响应"""
    period_start: date
    period_end: date
    total_analyzed: int
    top_causes: List[RootCauseAnalysis]
    recommendations: List[str]


class ProjectImpactItem(BaseModel):
    """项目影响项"""
    project_id: int
    project_name: str
    alert_count: int
    total_shortage_qty: Decimal
    estimated_delay_days: int
    estimated_cost_impact: Decimal
    critical_materials: List[str]


class ProjectImpactResponse(BaseModel):
    """项目影响响应"""
    total_projects: int
    items: List[ProjectImpactItem]


class NotificationSubscribeRequest(BaseModel):
    """订阅通知请求"""
    alert_levels: List[str] = Field(description="订阅的预警级别")
    project_ids: Optional[List[int]] = Field(None, description="订阅的项目ID列表")
    material_ids: Optional[List[int]] = Field(None, description="订阅的物料ID列表")
    notification_channels: List[str] = Field(['EMAIL'], description="通知渠道: EMAIL/SMS/WECHAT")
    enabled: bool = Field(True, description="是否启用")


class NotificationSubscribeResponse(BaseModel):
    """订阅通知响应"""
    subscription_id: int
    user_id: int
    alert_levels: List[str]
    project_ids: Optional[List[int]]
    material_ids: Optional[List[int]]
    notification_channels: List[str]
    enabled: bool
    created_at: datetime
