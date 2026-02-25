"""
售前AI成本估算 Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime


# ============= 成本估算 Schemas =============

class CostBreakdown(BaseModel):
    """成本分解详情"""
    hardware_cost: Decimal = Field(default=0, description="硬件成本")
    software_cost: Decimal = Field(default=0, description="软件成本")
    installation_cost: Decimal = Field(default=0, description="安装调试成本")
    service_cost: Decimal = Field(default=0, description="售后服务成本")
    risk_reserve: Decimal = Field(default=0, description="风险储备金")
    total_cost: Decimal = Field(description="总成本")


class PricingRecommendation(BaseModel):
    """定价推荐"""
    low: Decimal = Field(description="低价档报价")
    medium: Decimal = Field(description="中价档报价(推荐)")
    high: Decimal = Field(description="高价档报价")
    suggested_price: Decimal = Field(description="建议报价")
    target_margin_rate: Decimal = Field(description="目标毛利率(%)")
    market_analysis: Optional[str] = Field(None, description="市场分析")


class OptimizationSuggestion(BaseModel):
    """优化建议"""
    type: str = Field(description="优化类型")
    description: str = Field(description="建议描述")
    original_cost: Decimal = Field(description="原始成本")
    optimized_cost: Decimal = Field(description="优化后成本")
    saving_amount: Decimal = Field(description="节省金额")
    saving_rate: Decimal = Field(description="节省比例(%)")
    feasibility_score: Optional[Decimal] = Field(None, description="可行性评分")
    alternative_solutions: Optional[List[str]] = Field(None, description="替代方案")


class CostEstimationInput(BaseModel):
    """成本估算输入"""
    presale_ticket_id: int = Field(description="售前工单ID")
    solution_id: Optional[int] = Field(None, description="解决方案ID")
    
    # 项目基本信息
    project_type: str = Field(description="项目类型")
    industry: Optional[str] = Field(None, description="行业")
    complexity_level: str = Field(default="medium", description="复杂度(low/medium/high)")
    
    # 硬件信息
    hardware_items: Optional[List[Dict[str, Any]]] = Field(None, description="硬件清单")
    
    # 软件信息
    software_requirements: Optional[str] = Field(None, description="软件需求描述")
    estimated_man_days: Optional[int] = Field(None, description="预估人天")
    
    # 其他信息
    installation_difficulty: Optional[str] = Field(None, description="安装难度")
    service_years: Optional[int] = Field(1, description="售后服务年限")
    
    # 定价参数
    target_margin_rate: Optional[Decimal] = Field(Decimal("0.30"), description="目标毛利率(默认30%)")


class CostEstimationResponse(BaseModel):
    """成本估算结果"""
    id: int
    presale_ticket_id: int
    solution_id: Optional[int]
    
    # 成本分解
    cost_breakdown: CostBreakdown
    
    # AI分析
    optimization_suggestions: Optional[List[OptimizationSuggestion]]
    pricing_recommendations: Optional[PricingRecommendation]
    confidence_score: Optional[Decimal]
    
    # 元数据
    model_version: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= 成本优化 Schemas =============

class CostOptimizationInput(BaseModel):
    """成本优化输入"""
    estimation_id: int = Field(description="估算记录ID")
    focus_areas: Optional[List[str]] = Field(None, description="重点优化领域")
    max_risk_level: Optional[str] = Field("medium", description="最大风险接受度(low/medium/high)")


class CostOptimizationResponse(BaseModel):
    """成本优化结果"""
    original_total_cost: Decimal
    optimized_total_cost: Decimal
    total_saving: Decimal
    total_saving_rate: Decimal
    suggestions: List[OptimizationSuggestion]
    feasibility_summary: str


# ============= 定价推荐 Schemas =============

class PricingInput(BaseModel):
    """定价推荐输入"""
    estimation_id: int = Field(description="估算记录ID")
    target_margin_rate: Optional[Decimal] = Field(Decimal("0.30"), description="目标毛利率")
    market_competition_level: Optional[str] = Field("medium", description="市场竞争程度")
    customer_budget: Optional[Decimal] = Field(None, description="客户预算")


class PricingResponse(BaseModel):
    """定价推荐结果"""
    cost_base: Decimal
    pricing_recommendations: PricingRecommendation
    sensitivity_analysis: Optional[Dict[str, Any]]
    competitiveness_score: Optional[Decimal]


# ============= 成本对比 Schemas =============

class CostComparisonInput(BaseModel):
    """成本对比输入"""
    estimation_ids: List[int] = Field(description="估算记录ID列表(2-5个)")


class CostComparisonItem(BaseModel):
    """成本对比项"""
    estimation_id: int
    presale_ticket_id: int
    total_cost: Decimal
    cost_breakdown: CostBreakdown
    confidence_score: Optional[Decimal]


class CostComparisonResponse(BaseModel):
    """成本对比结果"""
    items: List[CostComparisonItem]
    comparison_summary: Dict[str, Any]
    recommendations: Optional[str]


# ============= 历史准确度 Schemas =============

class HistoricalAccuracyResponse(BaseModel):
    """历史准确度响应"""
    total_predictions: int
    average_variance_rate: Decimal
    accuracy_rate: Decimal  # 偏差<15%的比例
    best_performing_category: Optional[str]
    worst_performing_category: Optional[str]
    recent_trend: str  # improving/stable/declining
    sample_cases: Optional[List[Dict[str, Any]]]


class UpdateActualCostInput(BaseModel):
    """更新实际成本输入"""
    estimation_id: int = Field(description="估算记录ID")
    project_id: Optional[int] = Field(None, description="项目ID")
    project_name: Optional[str] = Field(None, description="项目名称")
    actual_cost: Decimal = Field(description="实际总成本")
    actual_breakdown: Optional[CostBreakdown] = Field(None, description="实际成本分解")


class UpdateActualCostResponse(BaseModel):
    """更新实际成本响应"""
    history_id: int
    variance_rate: Decimal
    variance_analysis: Dict[str, Any]
    learning_applied: bool
    message: str
