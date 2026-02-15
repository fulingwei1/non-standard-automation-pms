# -*- coding: utf-8 -*-
"""
资源冲突智能调度系统 - Pydantic Schemas
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# 资源冲突检测 Schemas
# ============================================================================

class ResourceConflictDetectionBase(BaseModel):
    """资源冲突检测基础Schema"""
    
    conflict_type: str = Field(default="PERSON", description="冲突类型: PERSON/DEVICE/WORKLOAD")
    conflict_code: str = Field(..., description="冲突编码")
    conflict_name: str = Field(..., description="冲突名称")
    
    resource_id: int = Field(..., description="资源ID")
    resource_type: str = Field(..., description="资源类型: PERSON/DEVICE")
    resource_name: Optional[str] = None
    department_name: Optional[str] = None
    
    # 项目A
    project_a_id: int
    allocation_a_id: Optional[int] = None
    allocation_a_percent: Optional[Decimal] = None
    start_date_a: Optional[date] = None
    end_date_a: Optional[date] = None
    
    # 项目B
    project_b_id: int
    allocation_b_id: Optional[int] = None
    allocation_b_percent: Optional[Decimal] = None
    start_date_b: Optional[date] = None
    end_date_b: Optional[date] = None
    
    # 冲突时间
    overlap_start: date
    overlap_end: date
    overlap_days: Optional[int] = None
    
    # 冲突程度
    total_allocation: Decimal = Field(..., description="总分配比例")
    over_allocation: Optional[Decimal] = None
    severity: str = Field(default="MEDIUM", description="严重程度")
    priority_score: int = Field(default=50, ge=0, le=100)
    
    # 工作负载
    planned_hours_a: Optional[Decimal] = None
    planned_hours_b: Optional[Decimal] = None
    total_planned_hours: Optional[Decimal] = None
    weekly_capacity: Decimal = Field(default=Decimal("40.0"))
    workload_ratio: Optional[Decimal] = None
    
    # AI检测
    detected_by: str = Field(default="SYSTEM")
    ai_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    ai_risk_factors: Optional[str] = None
    ai_impact_analysis: Optional[str] = None
    
    remark: Optional[str] = None


class ResourceConflictDetectionCreate(ResourceConflictDetectionBase):
    """创建资源冲突检测"""
    pass


class ResourceConflictDetectionUpdate(BaseModel):
    """更新资源冲突检测"""
    
    status: Optional[str] = None
    is_resolved: Optional[bool] = None
    resolution_method: Optional[str] = None
    resolution_note: Optional[str] = None
    severity: Optional[str] = None
    priority_score: Optional[int] = Field(None, ge=0, le=100)
    remark: Optional[str] = None


class ResourceConflictDetectionInDB(ResourceConflictDetectionBase):
    """数据库中的资源冲突检测"""
    
    id: int
    project_a_code: Optional[str] = None
    project_a_name: Optional[str] = None
    project_b_code: Optional[str] = None
    project_b_name: Optional[str] = None
    
    status: str
    is_resolved: bool
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None
    resolution_note: Optional[str] = None
    
    has_ai_suggestion: bool
    suggested_solution_id: Optional[int] = None
    
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    notified_users: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# AI调度方案推荐 Schemas
# ============================================================================

class ResourceSchedulingSuggestionBase(BaseModel):
    """AI调度方案推荐基础Schema"""
    
    conflict_id: int = Field(..., description="冲突ID")
    suggestion_code: str = Field(..., description="方案编码")
    suggestion_name: str = Field(..., description="方案名称")
    
    solution_type: str = Field(..., description="方案类型: RESCHEDULE/REALLOCATE/HIRE/OVERTIME/PRIORITIZE")
    solution_category: str = Field(default="AI", description="方案来源")
    
    strategy_name: Optional[str] = None
    strategy_description: Optional[str] = None
    
    adjustments: str = Field(..., description="调整详情(JSON)")
    
    # AI评分
    ai_score: Decimal = Field(..., ge=0, le=100, description="AI综合评分")
    feasibility_score: Optional[Decimal] = Field(None, ge=0, le=100)
    impact_score: Optional[Decimal] = Field(None, ge=0, le=100)
    cost_score: Optional[Decimal] = Field(None, ge=0, le=100)
    risk_score: Optional[Decimal] = Field(None, ge=0, le=100)
    efficiency_score: Optional[Decimal] = Field(None, ge=0, le=100)
    
    # 分析
    pros: Optional[str] = None
    cons: Optional[str] = None
    risks: Optional[str] = None
    
    # 影响
    affected_projects: Optional[str] = None
    affected_resources: Optional[str] = None
    timeline_impact_days: Optional[int] = None
    cost_impact: Optional[Decimal] = None
    quality_impact: Optional[str] = None
    
    # 资源需求
    additional_resources_needed: Optional[str] = None
    skill_requirements: Optional[str] = None
    
    # 执行计划
    execution_steps: Optional[str] = None
    estimated_duration_days: Optional[int] = None
    prerequisites: Optional[str] = None
    
    # AI信息
    ai_reasoning: Optional[str] = None
    ai_model: str = Field(default="GLM-5")
    ai_version: Optional[str] = None
    
    # 排名
    rank_order: int = Field(default=1, ge=1)
    is_recommended: bool = Field(default=False)
    recommendation_reason: Optional[str] = None
    
    remark: Optional[str] = None


class ResourceSchedulingSuggestionCreate(ResourceSchedulingSuggestionBase):
    """创建AI调度方案推荐"""
    pass


class ResourceSchedulingSuggestionUpdate(BaseModel):
    """更新AI调度方案推荐"""
    
    status: Optional[str] = None
    review_comment: Optional[str] = None
    implementation_result: Optional[str] = None
    user_rating: Optional[int] = Field(None, ge=1, le=5)
    user_feedback: Optional[str] = None
    actual_effectiveness: Optional[Decimal] = Field(None, ge=0, le=100)
    remark: Optional[str] = None


class ResourceSchedulingSuggestionInDB(ResourceSchedulingSuggestionBase):
    """数据库中的AI调度方案推荐"""
    
    id: int
    ai_generated_at: Optional[datetime] = None
    ai_tokens_used: Optional[int] = None
    
    status: str
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_comment: Optional[str] = None
    
    implemented_by: Optional[int] = None
    implemented_at: Optional[datetime] = None
    implementation_result: Optional[str] = None
    
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    actual_effectiveness: Optional[Decimal] = None
    
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 资源需求预测 Schemas
# ============================================================================

class ResourceDemandForecastBase(BaseModel):
    """资源需求预测基础Schema"""
    
    forecast_code: str = Field(..., description="预测编码")
    forecast_name: str = Field(..., description="预测名称")
    forecast_period: str = Field(..., description="预测周期: 1MONTH/3MONTH/6MONTH/1YEAR")
    
    forecast_start_date: date
    forecast_end_date: date
    
    resource_type: str = Field(..., description="资源类型: PERSON/DEVICE/SKILL")
    skill_category: Optional[str] = None
    skill_level: Optional[str] = None
    
    current_supply: Optional[int] = None
    predicted_demand: Optional[int] = None
    demand_gap: Optional[int] = None
    gap_severity: Optional[str] = None
    
    predicted_total_hours: Optional[Decimal] = None
    predicted_peak_hours: Optional[Decimal] = None
    predicted_avg_weekly_hours: Optional[Decimal] = None
    
    predicted_utilization: Optional[Decimal] = None
    peak_utilization: Optional[Decimal] = None
    low_utilization_periods: Optional[str] = None
    
    driving_projects: Optional[str] = None
    project_count: Optional[int] = None
    
    ai_model: str = Field(default="GLM-5")
    ai_confidence: Optional[Decimal] = Field(None, ge=0, le=1)
    prediction_factors: Optional[str] = None
    historical_trend: Optional[str] = None
    seasonality_pattern: Optional[str] = None
    
    recommendations: Optional[str] = None
    hiring_suggestion: Optional[str] = None
    training_suggestion: Optional[str] = None
    outsourcing_suggestion: Optional[str] = None
    
    estimated_cost: Optional[Decimal] = None
    cost_breakdown: Optional[str] = None
    
    risk_level: str = Field(default="LOW")
    risk_factors: Optional[str] = None
    mitigation_plan: Optional[str] = None
    
    remark: Optional[str] = None


class ResourceDemandForecastCreate(ResourceDemandForecastBase):
    """创建资源需求预测"""
    pass


class ResourceDemandForecastUpdate(BaseModel):
    """更新资源需求预测"""
    
    status: Optional[str] = None
    accuracy_rating: Optional[Decimal] = Field(None, ge=0, le=100)
    remark: Optional[str] = None


class ResourceDemandForecastInDB(ResourceDemandForecastBase):
    """数据库中的资源需求预测"""
    
    id: int
    generated_at: datetime
    status: str
    accuracy_rating: Optional[Decimal] = None
    
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 资源利用率分析 Schemas
# ============================================================================

class ResourceUtilizationAnalysisBase(BaseModel):
    """资源利用率分析基础Schema"""
    
    analysis_code: str = Field(..., description="分析编码")
    analysis_name: str = Field(..., description="分析名称")
    analysis_period: str = Field(..., description="分析周期: DAILY/WEEKLY/MONTHLY/QUARTERLY")
    
    period_start_date: date
    period_end_date: date
    period_days: Optional[int] = None
    
    resource_id: int
    resource_type: str = Field(..., description="资源类型: PERSON/DEVICE")
    resource_name: Optional[str] = None
    department_name: Optional[str] = None
    skill_category: Optional[str] = None
    
    total_available_hours: Optional[Decimal] = None
    total_allocated_hours: Optional[Decimal] = None
    total_actual_hours: Optional[Decimal] = None
    total_idle_hours: Optional[Decimal] = None
    total_overtime_hours: Optional[Decimal] = None
    
    utilization_rate: Optional[Decimal] = None
    allocation_rate: Optional[Decimal] = None
    efficiency_rate: Optional[Decimal] = None
    idle_rate: Optional[Decimal] = None
    overtime_rate: Optional[Decimal] = None
    
    utilization_status: Optional[str] = None
    is_idle_resource: bool = Field(default=False)
    is_overloaded: bool = Field(default=False)
    
    project_count: Optional[int] = None
    active_projects: Optional[str] = None
    project_distribution: Optional[str] = None
    
    daily_utilization: Optional[str] = None
    weekly_utilization: Optional[str] = None
    peak_utilization_date: Optional[date] = None
    low_utilization_periods: Optional[str] = None
    
    ai_insights: Optional[str] = None
    optimization_suggestions: Optional[str] = None
    reallocation_opportunities: Optional[str] = None
    
    labor_cost: Optional[Decimal] = None
    idle_cost: Optional[Decimal] = None
    overtime_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    cost_efficiency: Optional[Decimal] = None
    
    previous_period_utilization: Optional[Decimal] = None
    utilization_change: Optional[Decimal] = None
    trend: Optional[str] = None
    
    has_alert: bool = Field(default=False)
    alert_type: Optional[str] = None
    alert_message: Optional[str] = None
    
    remark: Optional[str] = None


class ResourceUtilizationAnalysisCreate(ResourceUtilizationAnalysisBase):
    """创建资源利用率分析"""
    pass


class ResourceUtilizationAnalysisUpdate(BaseModel):
    """更新资源利用率分析"""
    
    utilization_status: Optional[str] = None
    is_idle_resource: Optional[bool] = None
    is_overloaded: Optional[bool] = None
    has_alert: Optional[bool] = None
    remark: Optional[str] = None


class ResourceUtilizationAnalysisInDB(ResourceUtilizationAnalysisBase):
    """数据库中的资源利用率分析"""
    
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 调度操作日志 Schemas
# ============================================================================

class ResourceSchedulingLogCreate(BaseModel):
    """创建调度操作日志"""
    
    conflict_id: Optional[int] = None
    suggestion_id: Optional[int] = None
    
    action_type: str = Field(..., description="操作类型")
    action_desc: Optional[str] = None
    
    operator_id: Optional[int] = None
    operator_name: Optional[str] = None
    operator_role: Optional[str] = None
    
    result: Optional[str] = None
    result_data: Optional[str] = None
    error_message: Optional[str] = None
    
    execution_time_ms: Optional[int] = None
    ai_tokens_used: Optional[int] = None
    
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class ResourceSchedulingLogInDB(ResourceSchedulingLogCreate):
    """数据库中的调度操作日志"""
    
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# 请求/响应 Schemas
# ============================================================================

class ConflictDetectionRequest(BaseModel):
    """冲突检测请求"""
    
    resource_id: Optional[int] = None
    resource_type: Optional[str] = None
    project_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    auto_generate_suggestions: bool = Field(default=True, description="是否自动生成调度方案")


class ConflictDetectionResponse(BaseModel):
    """冲突检测响应"""
    
    total_conflicts: int
    new_conflicts: int
    critical_conflicts: int
    conflicts: List[ResourceConflictDetectionInDB]
    suggestions_generated: int = 0
    detection_time_ms: int


class AISchedulingSuggestionRequest(BaseModel):
    """AI调度方案生成请求"""
    
    conflict_id: int
    max_suggestions: int = Field(default=3, ge=1, le=5, description="最多生成方案数")
    prefer_minimal_impact: bool = Field(default=True, description="优先低影响方案")
    include_reasoning: bool = Field(default=True, description="包含推理过程")


class AISchedulingSuggestionResponse(BaseModel):
    """AI调度方案生成响应"""
    
    conflict_id: int
    suggestions: List[ResourceSchedulingSuggestionInDB]
    recommended_suggestion_id: Optional[int] = None
    generation_time_ms: int
    ai_tokens_used: int


class ForecastRequest(BaseModel):
    """需求预测请求"""
    
    forecast_period: str = Field(..., description="预测周期: 1MONTH/3MONTH/6MONTH/1YEAR")
    resource_type: str = Field(default="PERSON", description="资源类型")
    skill_category: Optional[str] = None
    include_recommendations: bool = Field(default=True, description="包含建议措施")


class ForecastResponse(BaseModel):
    """需求预测响应"""
    
    forecasts: List[ResourceDemandForecastInDB]
    critical_gaps: int
    total_hiring_needed: int
    total_training_needed: int
    generation_time_ms: int


class UtilizationAnalysisRequest(BaseModel):
    """利用率分析请求"""
    
    resource_id: Optional[int] = None
    department: Optional[str] = None
    start_date: date
    end_date: date
    analysis_period: str = Field(default="WEEKLY", description="分析周期")
    identify_idle: bool = Field(default=True, description="识别闲置资源")
    identify_overloaded: bool = Field(default=True, description="识别超负荷资源")


class UtilizationAnalysisResponse(BaseModel):
    """利用率分析响应"""
    
    analyses: List[ResourceUtilizationAnalysisInDB]
    idle_resources_count: int
    overloaded_resources_count: int
    avg_utilization: Decimal
    optimization_opportunities: int
    analysis_time_ms: int


class DashboardSummary(BaseModel):
    """资源调度仪表板摘要"""
    
    total_conflicts: int
    critical_conflicts: int
    unresolved_conflicts: int
    
    total_suggestions: int
    pending_suggestions: int
    implemented_suggestions: int
    
    idle_resources: int
    overloaded_resources: int
    avg_utilization: Decimal
    
    forecasts_count: int
    critical_gaps: int
    hiring_needed: int
    
    last_detection_time: Optional[datetime] = None
    last_analysis_time: Optional[datetime] = None
