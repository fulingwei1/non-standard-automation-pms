"""
项目对比分析Schema
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class ComparisonRequest(BaseModel):
    """对比分析请求"""
    review_id: int = Field(..., description="复盘报告ID")
    similarity_type: str = Field(default="industry", description="相似度类型：industry/type/scale")
    comparison_limit: int = Field(default=5, ge=1, le=10, description="对比项目数量")


class ComparisonMetrics(BaseModel):
    """对比指标"""
    schedule_variance: float
    cost_variance: float
    change_count: float
    customer_satisfaction: float


class VarianceAnalysis(BaseModel):
    """差异分析"""
    schedule: float
    cost: float
    changes: float
    satisfaction: float


class ComparisonItem(BaseModel):
    """对比项"""
    area: str
    description: str
    reason: Optional[str] = None
    cause: Optional[str] = None


class ImprovementItem(BaseModel):
    """改进项"""
    area: str
    problem: str
    suggestion: str
    expected_impact: str
    priority: str = "MEDIUM"
    feasibility: str = "HIGH"
    estimated_impact: float = 0.5


class BenchmarkItem(BaseModel):
    """基准项"""
    target: float
    actual: float
    gap: float
    status: str  # ABOVE/BELOW/MEET


class ComparisonResponse(BaseModel):
    """对比分析响应"""
    success: bool
    review_id: int
    current_metrics: ComparisonMetrics
    historical_average: ComparisonMetrics
    variance_analysis: VarianceAnalysis
    strengths: List[ComparisonItem]
    weaknesses: List[ComparisonItem]
    improvements: List[ImprovementItem]
    benchmarks: Dict[str, BenchmarkItem]
    similar_projects_count: int


class ImprovementResponse(BaseModel):
    """改进建议响应"""
    success: bool
    review_id: int
    improvements: List[ImprovementItem]
    total_count: int
