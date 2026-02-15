"""
AI情绪分析相关Schema
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


# ==================== 情绪分析相关 ====================

class EmotionAnalysisRequest(BaseModel):
    """情绪分析请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    customer_id: int = Field(..., description="客户ID")
    communication_content: str = Field(..., min_length=1, description="沟通内容")
    
    @field_validator('communication_content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("沟通内容不能为空")
        return v.strip()


class EmotionAnalysisResponse(BaseModel):
    """情绪分析响应"""
    id: int
    presale_ticket_id: int
    customer_id: int
    sentiment: str  # positive/neutral/negative
    purchase_intent_score: float = Field(..., ge=0, le=100, description="购买意向评分")
    churn_risk: str  # high/medium/low
    emotion_factors: Dict[str, Any]
    analysis_result: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 流失预警相关 ====================

class ChurnRiskPredictionRequest(BaseModel):
    """流失风险预测请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    customer_id: int = Field(..., description="客户ID")
    recent_communications: List[str] = Field(..., min_length=1, description="最近的沟通记录")
    days_since_last_contact: Optional[int] = Field(None, ge=0, description="距离上次联系的天数")
    response_time_trend: Optional[List[float]] = Field(None, description="回复时间趋势(小时)")


class ChurnRiskPredictionResponse(BaseModel):
    """流失风险预测响应"""
    presale_ticket_id: int
    customer_id: int
    churn_risk: str  # high/medium/low
    risk_score: float = Field(..., ge=0, le=100, description="流失风险评分")
    risk_factors: List[Dict[str, Any]]
    retention_strategies: List[str]
    analysis_summary: str


# ==================== 跟进提醒相关 ====================

class FollowUpRecommendationRequest(BaseModel):
    """跟进时机推荐请求"""
    presale_ticket_id: int = Field(..., description="售前工单ID")
    customer_id: int = Field(..., description="客户ID")
    latest_emotion_analysis_id: Optional[int] = Field(None, description="最新情绪分析ID")


class FollowUpRecommendationResponse(BaseModel):
    """跟进时机推荐响应"""
    id: int
    presale_ticket_id: int
    recommended_time: datetime
    priority: str  # high/medium/low
    follow_up_content: str
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FollowUpReminderListResponse(BaseModel):
    """跟进提醒列表响应"""
    total: int
    reminders: List[FollowUpRecommendationResponse]


class DismissReminderRequest(BaseModel):
    """忽略提醒请求"""
    reminder_id: int = Field(..., description="提醒ID")


# ==================== 情绪趋势相关 ====================

class EmotionTrendResponse(BaseModel):
    """情绪趋势响应"""
    id: int
    presale_ticket_id: int
    customer_id: int
    trend_data: List[Dict[str, Any]]
    key_turning_points: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== 批量分析相关 ====================

class BatchAnalysisRequest(BaseModel):
    """批量分析请求"""
    customer_ids: List[int] = Field(..., min_length=1, max_length=100, description="客户ID列表")
    analysis_type: str = Field(default="full", description="分析类型: full/emotion/churn")
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        allowed_types = ['full', 'emotion', 'churn']
        if v not in allowed_types:
            raise ValueError(f"分析类型必须是: {', '.join(allowed_types)}")
        return v


class CustomerAnalysisSummary(BaseModel):
    """客户分析摘要"""
    customer_id: int
    latest_sentiment: Optional[str] = None
    purchase_intent_score: Optional[float] = None
    churn_risk: Optional[str] = None
    needs_attention: bool
    recommended_action: str


class BatchAnalysisResponse(BaseModel):
    """批量分析响应"""
    total_analyzed: int
    success_count: int
    failed_count: int
    summaries: List[CustomerAnalysisSummary]
    analysis_timestamp: datetime


# ==================== 通用响应 ====================

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True
