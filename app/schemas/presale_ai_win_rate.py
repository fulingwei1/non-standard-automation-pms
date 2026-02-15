# -*- coding: utf-8 -*-
"""
售前AI赢率预测 - Schema定义
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class InfluencingFactor(BaseModel):
    """影响因素"""
    factor: str = Field(..., description="因素名称")
    impact: str = Field(..., description="影响类型: positive/negative/neutral")
    score: int = Field(..., ge=1, le=10, description="影响分数 1-10")
    description: str = Field(..., description="详细说明")


class CompetitorAnalysis(BaseModel):
    """竞品分析"""
    competitors: List[str] = Field(default_factory=list, description="竞争对手列表")
    our_advantages: List[str] = Field(default_factory=list, description="我方优势")
    competitor_advantages: List[str] = Field(default_factory=list, description="竞对优势")
    differentiation_strategy: List[str] = Field(default_factory=list, description="差异化策略建议")


class ImprovementSuggestions(BaseModel):
    """改进建议"""
    short_term: List[str] = Field(default_factory=list, description="短期行动清单（1周内）")
    mid_term: List[str] = Field(default_factory=list, description="中期策略（1个月内）")
    milestones: List[str] = Field(default_factory=list, description="关键里程碑监控")


class PredictWinRateRequest(BaseModel):
    """预测赢率请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    
    # 基本信息
    ticket_no: Optional[str] = Field(None, description="工单编号")
    title: Optional[str] = Field(None, description="工单标题")
    customer_name: Optional[str] = Field(None, description="客户名称")
    estimated_amount: Optional[Decimal] = Field(None, description="预估金额")
    ticket_type: Optional[str] = Field(None, description="工单类型")
    urgency: Optional[str] = Field(None, description="紧急程度")
    
    # 客户信息
    is_repeat_customer: bool = Field(False, description="是否老客户")
    cooperation_count: int = Field(0, description="历史合作次数")
    success_count: int = Field(0, description="历史成功次数")
    
    # 竞争态势
    competitor_count: int = Field(3, description="竞争对手数量")
    main_competitors: Optional[str] = Field(None, description="主要竞争对手")
    
    # 技术评估
    requirement_maturity: Optional[int] = Field(None, description="需求成熟度")
    technical_feasibility: Optional[int] = Field(None, description="技术可行性")
    business_feasibility: Optional[int] = Field(None, description="商务可行性")
    delivery_risk: Optional[int] = Field(None, description="交付风险")
    customer_relationship: Optional[int] = Field(None, description="客户关系")
    
    # 销售人员
    salesperson_id: Optional[int] = Field(None, description="销售人员ID")
    salesperson_win_rate: Optional[float] = Field(None, description="销售人员历史赢率")


class WinRatePredictionResponse(BaseModel):
    """赢率预测响应"""
    id: int = Field(..., description="预测记录ID")
    presale_ticket_id: int = Field(..., description="售前工单ID")
    win_rate_score: Decimal = Field(..., description="赢率分数 (0-100)")
    confidence_interval: str = Field(..., description="置信区间")
    influencing_factors: List[Dict[str, Any]] = Field(default_factory=list, description="影响因素")
    competitor_analysis: Dict[str, Any] = Field(default_factory=dict, description="竞品分析")
    improvement_suggestions: Dict[str, Any] = Field(default_factory=dict, description="改进建议")
    ai_analysis_report: Optional[str] = Field(None, description="AI分析报告")
    model_version: Optional[str] = Field(None, description="模型版本")
    predicted_at: datetime = Field(..., description="预测时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    
    class Config:
        from_attributes = True


class UpdateActualResultRequest(BaseModel):
    """更新实际结果请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    actual_result: str = Field(..., description="实际结果: won/lost/pending")
    win_date: Optional[datetime] = Field(None, description="赢单日期")
    lost_date: Optional[datetime] = Field(None, description="失单日期")


class ModelAccuracyResponse(BaseModel):
    """模型准确度响应"""
    overall_accuracy: float = Field(..., description="总体准确率 (%)")
    total_predictions: int = Field(..., description="总预测数")
    correct_predictions: int = Field(..., description="正确预测数")
    average_error: float = Field(..., description="平均预测误差")
    by_result: Dict[str, Any] = Field(default_factory=dict, description="按结果分组统计")
    last_updated: str = Field(..., description="最后更新时间")


__all__ = [
    "PredictWinRateRequest",
    "WinRatePredictionResponse",
    "UpdateActualResultRequest",
    "ModelAccuracyResponse",
    "InfluencingFactor",
    "CompetitorAnalysis",
    "ImprovementSuggestions",
]
