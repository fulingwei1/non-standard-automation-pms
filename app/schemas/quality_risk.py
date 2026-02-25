# -*- coding: utf-8 -*-
"""
质量风险识别系统 Pydantic Schema
"""

from datetime import date, datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ==================== 质量风险检测 Schema ====================

class QualityRiskDetectionBase(BaseModel):
    """质量风险检测基础Schema"""
    project_id: int = Field(..., description="项目ID")
    module_name: Optional[str] = Field(None, description="模块名称")
    task_id: Optional[int] = Field(None, description="任务ID")
    detection_date: date = Field(..., description="检测日期")
    source_type: str = Field(..., description="数据来源类型: WORK_LOG/PROGRESS/MANUAL")
    source_id: Optional[int] = Field(None, description="来源记录ID")


class QualityRiskDetectionCreate(QualityRiskDetectionBase):
    """创建质量风险检测"""
    risk_signals: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    risk_keywords: Optional[Dict[str, List[str]]] = Field(default_factory=dict)
    abnormal_patterns: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    risk_level: str = Field(..., description="风险等级")
    risk_score: float = Field(..., ge=0, le=100, description="风险评分")
    risk_category: Optional[str] = Field(None, description="风险类别")
    predicted_issues: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    rework_probability: Optional[float] = Field(None, ge=0, le=100)
    estimated_impact_days: Optional[int] = Field(None, ge=0)
    ai_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ai_confidence: Optional[float] = Field(None, ge=0, le=100)
    analysis_model: Optional[str] = Field(None)


class QualityRiskDetectionUpdate(BaseModel):
    """更新质量风险检测"""
    status: Optional[str] = None
    confirmed_by: Optional[int] = None
    resolution_note: Optional[str] = None


class QualityRiskDetectionResponse(QualityRiskDetectionBase):
    """质量风险检测响应"""
    id: int
    risk_signals: Optional[List[Dict[str, Any]]] = None
    risk_keywords: Optional[Dict[str, List[str]]] = None
    abnormal_patterns: Optional[List[Dict[str, Any]]] = None
    risk_level: str
    risk_score: float
    risk_category: Optional[str] = None
    predicted_issues: Optional[List[Dict[str, Any]]] = None
    rework_probability: Optional[float] = None
    estimated_impact_days: Optional[int] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    ai_confidence: Optional[float] = None
    analysis_model: Optional[str] = None
    status: str
    confirmed_by: Optional[int] = None
    confirmed_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 测试推荐 Schema ====================

class QualityTestRecommendationBase(BaseModel):
    """测试推荐基础Schema"""
    project_id: int = Field(..., description="项目ID")
    detection_id: Optional[int] = Field(None, description="关联的风险检测ID")
    recommendation_date: date = Field(..., description="推荐日期")


class QualityTestRecommendationCreate(QualityTestRecommendationBase):
    """创建测试推荐"""
    focus_areas: List[Dict[str, Any]] = Field(..., description="测试重点区域")
    priority_modules: Optional[List[str]] = Field(default_factory=list)
    risk_modules: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    test_types: Optional[List[str]] = Field(default_factory=list)
    test_scenarios: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    test_coverage_target: Optional[float] = Field(None, ge=0, le=100)
    recommended_testers: Optional[int] = Field(None, ge=1)
    recommended_days: Optional[int] = Field(None, ge=1)
    priority_level: str = Field(..., description="优先级")
    ai_reasoning: Optional[str] = None
    risk_summary: Optional[str] = None
    historical_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class QualityTestRecommendationUpdate(BaseModel):
    """更新测试推荐"""
    status: Optional[str] = None
    acceptance_note: Optional[str] = None
    actual_test_days: Optional[int] = None
    actual_coverage: Optional[float] = Field(None, ge=0, le=100)
    bugs_found: Optional[int] = Field(None, ge=0)
    critical_bugs_found: Optional[int] = Field(None, ge=0)
    recommendation_accuracy: Optional[float] = Field(None, ge=0, le=100)


class QualityTestRecommendationResponse(QualityTestRecommendationBase):
    """测试推荐响应"""
    id: int
    focus_areas: List[Dict[str, Any]]
    priority_modules: Optional[List[str]] = None
    risk_modules: Optional[List[Dict[str, Any]]] = None
    test_types: Optional[List[str]] = None
    test_scenarios: Optional[List[Dict[str, Any]]] = None
    test_coverage_target: Optional[float] = None
    recommended_testers: Optional[int] = None
    recommended_days: Optional[int] = None
    priority_level: str
    ai_reasoning: Optional[str] = None
    risk_summary: Optional[str] = None
    historical_data: Optional[Dict[str, Any]] = None
    test_plan_generated: bool
    test_plan_id: Optional[int] = None
    status: str
    acceptance_note: Optional[str] = None
    actual_test_days: Optional[int] = None
    actual_coverage: Optional[float] = None
    bugs_found: Optional[int] = None
    critical_bugs_found: Optional[int] = None
    recommendation_accuracy: Optional[float] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 分析请求 Schema ====================

class WorkLogAnalysisRequest(BaseModel):
    """工作日志分析请求"""
    project_id: int = Field(..., description="项目ID")
    start_date: Optional[date] = Field(None, description="开始日期")
    end_date: Optional[date] = Field(None, description="结束日期")
    module_name: Optional[str] = Field(None, description="模块名称")
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表")


class QualityReportRequest(BaseModel):
    """质量报告请求"""
    project_id: int = Field(..., description="项目ID")
    start_date: date = Field(..., description="开始日期")
    end_date: date = Field(..., description="结束日期")
    include_recommendations: bool = Field(True, description="是否包含测试推荐")


class QualityReportResponse(BaseModel):
    """质量报告响应"""
    project_id: int
    project_name: str
    report_period: str
    overall_risk_level: str
    total_detections: int
    risk_distribution: Dict[str, int]
    top_risk_modules: List[Dict[str, Any]]
    trend_analysis: Dict[str, Any]
    recommendations: Optional[List[Dict[str, Any]]] = None
    summary: str
    generated_at: datetime

    class Config:
        from_attributes = True
