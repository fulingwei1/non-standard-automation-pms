# -*- coding: utf-8 -*-
"""
AI项目规划助手 - Pydantic Schemas
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field


# ========== 项目计划 ==========

class ProjectPlanRequest(BaseModel):
    """项目计划生成请求"""
    project_name: str = Field(..., description="项目名称")
    project_type: str = Field(..., description="项目类型")
    requirements: str = Field(..., description="项目需求描述")
    industry: Optional[str] = Field(None, description="行业")
    complexity: Optional[str] = Field("MEDIUM", description="复杂度: LOW/MEDIUM/HIGH/CRITICAL")
    use_template: bool = Field(True, description="是否使用已有模板")


class ProjectPlanResponse(BaseModel):
    """项目计划响应"""
    template_id: int
    template_code: str
    template_name: str
    estimated_duration_days: Optional[int]
    estimated_effort_hours: Optional[float]
    estimated_cost: Optional[float]
    confidence_score: Optional[float]
    phases: Optional[str] = None
    milestones: Optional[str] = None
    required_roles: Optional[str] = None
    risk_factors: Optional[str] = None
    
    class Config:
        from_attributes = True


# ========== WBS分解 ==========

class WbsDecompositionRequest(BaseModel):
    """WBS分解请求"""
    project_id: int = Field(..., description="项目ID")
    template_id: Optional[int] = Field(None, description="使用的模板ID")
    max_level: Optional[int] = Field(3, ge=1, le=5, description="最大分解层级")


class WbsSuggestionItem(BaseModel):
    """WBS建议项"""
    wbs_id: int
    wbs_code: str
    task_name: str
    level: int
    parent_id: Optional[int]
    estimated_duration_days: Optional[float]
    estimated_effort_hours: Optional[float] = None
    complexity: Optional[str] = None
    is_critical_path: bool = False


class WbsDecompositionResponse(BaseModel):
    """WBS分解响应"""
    project_id: int
    total_tasks: int
    suggestions: List[WbsSuggestionItem]


# ========== 资源分配 ==========

class ResourceAllocationRequest(BaseModel):
    """资源分配请求"""
    wbs_suggestion_id: int = Field(..., description="WBS建议ID")
    available_user_ids: Optional[List[int]] = Field(None, description="可用用户ID列表")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")


class ResourceAllocationItem(BaseModel):
    """资源分配项"""
    allocation_id: int
    user_id: int
    allocation_type: str
    overall_match_score: Optional[float]
    skill_match_score: Optional[float]
    availability_score: Optional[float]
    estimated_cost: Optional[float]
    recommendation_reason: Optional[str]


class ResourceAllocationResponse(BaseModel):
    """资源分配响应"""
    wbs_suggestion_id: int
    total_recommendations: int
    allocations: List[ResourceAllocationItem]


# ========== 进度排期 ==========

class ScheduleOptimizationRequest(BaseModel):
    """进度排期优化请求"""
    project_id: int = Field(..., description="项目ID")
    start_date: Optional[date] = Field(None, description="项目开始日期")
    constraints: Optional[Dict[str, Any]] = Field(None, description="约束条件")


class GanttTaskItem(BaseModel):
    """甘特图任务项"""
    task_id: int
    task_name: str
    wbs_code: str
    level: int
    parent_id: Optional[int]
    start_date: str
    end_date: str
    duration_days: Optional[float]
    is_critical: bool = False
    progress: float = 0


class ScheduleOptimizationResponse(BaseModel):
    """进度排期优化响应"""
    project_id: int
    start_date: str
    total_duration_days: float
    end_date: str
    gantt_data: List[Dict[str, Any]]
    critical_path: List[Dict[str, Any]]
    critical_path_length: int
    resource_load: Dict[int, Dict]
    conflicts: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    optimization_summary: Dict[str, Any]
