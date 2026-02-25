# -*- coding: utf-8 -*-
"""
变更影响智能分析系统 Schemas
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# 变更影响分析 Schemas
# ============================================================

class ChangeImpactAnalysisBase(BaseModel):
    """变更影响分析基础Schema"""
    analysis_version: str = Field(default="V1.0", description="分析版本")
    ai_model: str = Field(default="GLM-5", description="使用的AI模型")


class ChangeImpactAnalysisCreate(ChangeImpactAnalysisBase):
    """创建变更影响分析"""
    change_request_id: int = Field(..., description="变更请求ID")
    force_reanalysis: bool = Field(default=False, description="是否强制重新分析")


class ChangeImpactAnalysisResponse(ChangeImpactAnalysisBase):
    """变更影响分析响应"""
    id: int
    change_request_id: int
    analysis_status: str
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    analysis_duration_ms: Optional[int] = None
    ai_confidence_score: Optional[Decimal] = None
    
    # 进度影响
    schedule_impact_level: Optional[str] = None
    schedule_delay_days: Optional[int] = None
    schedule_affected_tasks_count: Optional[int] = None
    schedule_critical_path_affected: Optional[bool] = None
    schedule_milestone_affected: Optional[bool] = None
    schedule_impact_description: Optional[str] = None
    schedule_affected_tasks: Optional[List[Dict[str, Any]]] = None
    schedule_affected_milestones: Optional[List[Dict[str, Any]]] = None
    
    # 成本影响
    cost_impact_level: Optional[str] = None
    cost_impact_amount: Optional[Decimal] = None
    cost_impact_percentage: Optional[Decimal] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    cost_impact_description: Optional[str] = None
    cost_budget_exceeded: Optional[bool] = None
    cost_contingency_required: Optional[Decimal] = None
    
    # 质量影响
    quality_impact_level: Optional[str] = None
    quality_risk_areas: Optional[List[Dict[str, Any]]] = None
    quality_testing_impact: Optional[str] = None
    quality_acceptance_impact: Optional[str] = None
    quality_mitigation_required: Optional[bool] = None
    quality_impact_description: Optional[str] = None
    
    # 资源影响
    resource_impact_level: Optional[str] = None
    resource_additional_required: Optional[List[Dict[str, Any]]] = None
    resource_reallocation_needed: Optional[bool] = None
    resource_conflict_detected: Optional[bool] = None
    resource_impact_description: Optional[str] = None
    resource_affected_allocations: Optional[List[Dict[str, Any]]] = None
    
    # 连锁反应
    chain_reaction_detected: Optional[bool] = None
    chain_reaction_depth: Optional[int] = None
    chain_reaction_affected_projects: Optional[List[Dict[str, Any]]] = None
    dependency_tree: Optional[Dict[str, Any]] = None
    critical_dependencies: Optional[List[Dict[str, Any]]] = None
    
    # 综合风险
    overall_risk_score: Optional[Decimal] = None
    overall_risk_level: Optional[str] = None
    risk_factors: Optional[List[Dict[str, Any]]] = None
    recommended_action: Optional[str] = None
    
    # 分析摘要
    analysis_summary: Optional[str] = None
    analysis_details: Optional[Dict[str, Any]] = None
    
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChainReactionResponse(BaseModel):
    """连锁反应响应"""
    change_request_id: int
    detected: bool
    depth: int
    affected_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    affected_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    affected_projects: List[Dict[str, Any]] = Field(default_factory=list)
    dependency_tree: Optional[Dict[str, Any]] = None
    critical_dependencies: List[Dict[str, Any]] = Field(default_factory=list)


class ImpactReportResponse(BaseModel):
    """影响报告响应"""
    change_request_id: int
    report_generated_at: datetime
    summary: str
    overall_risk_level: str
    overall_risk_score: Decimal
    
    schedule_impact: Dict[str, Any]
    cost_impact: Dict[str, Any]
    quality_impact: Dict[str, Any]
    resource_impact: Dict[str, Any]
    chain_reactions: Dict[str, Any]
    
    recommendations: List[str]
    action_items: List[Dict[str, Any]]


# ============================================================
# 变更应对方案 Schemas
# ============================================================

class ChangeResponseSuggestionBase(BaseModel):
    """变更应对方案基础Schema"""
    suggestion_title: str = Field(..., min_length=1, max_length=200, description="方案标题")
    suggestion_type: str = Field(..., description="方案类型")
    suggestion_priority: int = Field(default=5, ge=1, le=10, description="优先级 (1-10)")
    summary: Optional[str] = Field(None, description="方案摘要")
    detailed_description: Optional[str] = Field(None, description="详细描述")


class ChangeResponseSuggestionCreate(ChangeResponseSuggestionBase):
    """创建应对方案"""
    change_request_id: int = Field(..., description="变更请求ID")
    impact_analysis_id: Optional[int] = Field(None, description="关联的影响分析ID")
    action_steps: Optional[List[Dict[str, Any]]] = Field(None, description="执行步骤")
    estimated_cost: Optional[Decimal] = Field(None, description="预估成本")
    estimated_duration_days: Optional[int] = Field(None, description="预估工期")
    resource_requirements: Optional[List[Dict[str, Any]]] = Field(None, description="资源需求")


class ChangeResponseSuggestionResponse(ChangeResponseSuggestionBase):
    """应对方案响应"""
    id: int
    change_request_id: int
    impact_analysis_id: Optional[int] = None
    suggestion_code: Optional[str] = None
    
    action_steps: Optional[List[Dict[str, Any]]] = None
    estimated_cost: Optional[Decimal] = None
    estimated_duration_days: Optional[int] = None
    resource_requirements: Optional[List[Dict[str, Any]]] = None
    dependencies: Optional[List[Dict[str, Any]]] = None
    
    risks: Optional[List[Dict[str, Any]]] = None
    opportunities: Optional[List[Dict[str, Any]]] = None
    risk_mitigation_plan: Optional[str] = None
    
    feasibility_score: Optional[Decimal] = None
    technical_feasibility: Optional[str] = None
    cost_feasibility: Optional[str] = None
    schedule_feasibility: Optional[str] = None
    feasibility_analysis: Optional[str] = None
    
    expected_outcomes: Optional[List[Dict[str, Any]]] = None
    success_criteria: Optional[List[Dict[str, Any]]] = None
    kpi_impacts: Optional[List[Dict[str, Any]]] = None
    
    ai_recommendation_score: Optional[Decimal] = None
    ai_confidence_level: Optional[str] = None
    ai_reasoning: Optional[str] = None
    alternative_suggestions: Optional[List[Dict[str, Any]]] = None
    
    status: str
    selected_at: Optional[datetime] = None
    selected_by: Optional[int] = None
    selection_reason: Optional[str] = None
    
    implementation_status: Optional[str] = None
    implementation_start_date: Optional[datetime] = None
    implementation_end_date: Optional[datetime] = None
    implementation_notes: Optional[str] = None
    actual_cost: Optional[Decimal] = None
    actual_duration_days: Optional[int] = None
    
    effectiveness_score: Optional[Decimal] = None
    lessons_learned: Optional[str] = None
    evaluation_notes: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    evaluated_by: Optional[int] = None
    
    attachments: Optional[List[Dict[str, Any]]] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SuggestionSelectRequest(BaseModel):
    """选择方案请求"""
    selection_reason: Optional[str] = Field(None, description="选择理由")


class SuggestionGenerateRequest(BaseModel):
    """生成方案请求"""
    change_request_id: int = Field(..., description="变更请求ID")
    impact_analysis_id: Optional[int] = Field(None, description="影响分析ID")
    max_suggestions: int = Field(default=3, ge=1, le=10, description="最大生成方案数")
    include_alternatives: bool = Field(default=True, description="是否包含备选方案")


# ============================================================
# 统计分析 Schemas
# ============================================================

class ImpactStatsResponse(BaseModel):
    """影响统计响应"""
    total_changes: int
    total_analyses: int
    
    by_risk_level: Dict[str, int]
    by_impact_type: Dict[str, Dict[str, int]]
    by_recommended_action: Dict[str, int]
    
    average_analysis_duration_ms: int
    average_risk_score: Decimal
    average_confidence_score: Decimal
    
    chain_reaction_rate: Decimal
    critical_path_impact_rate: Decimal
    budget_exceeded_rate: Decimal
    
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class ImpactTrendResponse(BaseModel):
    """影响趋势响应"""
    period: str
    data_points: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]


class HotImpactResponse(BaseModel):
    """高频影响点响应"""
    most_affected_tasks: List[Dict[str, Any]]
    most_affected_milestones: List[Dict[str, Any]]
    most_affected_projects: List[Dict[str, Any]]
    common_risk_factors: List[Dict[str, Any]]
    common_impact_patterns: List[Dict[str, Any]]


class EffectivenessResponse(BaseModel):
    """方案有效性响应"""
    total_suggestions: int
    selected_count: int
    implemented_count: int
    completed_count: int
    
    average_feasibility_score: Decimal
    average_effectiveness_score: Decimal
    average_ai_recommendation_score: Decimal
    
    by_type: Dict[str, Dict[str, Any]]
    success_rate: Decimal
    
    cost_accuracy: Dict[str, Any]
    duration_accuracy: Dict[str, Any]
    
    top_successful_patterns: List[Dict[str, Any]]
    lessons_learned: List[str]
