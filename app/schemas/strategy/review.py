# -*- coding: utf-8 -*-
"""
战略管理 Schema - 战略审视与日历事件
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..common import TimestampSchema


# ============================================
# StrategyReview - 战略审视
# ============================================

class StrategyReviewCreate(BaseModel):
    """创建战略审视"""
    strategy_id: int = Field(description="关联战略")
    review_type: str = Field(description="审视类型：ANNUAL/QUARTERLY/MONTHLY/SPECIAL")
    review_date: date = Field(description="审视日期")
    review_period: Optional[str] = Field(default=None, description="审视周期，如 2026-Q1")
    reviewer_id: Optional[int] = Field(default=None, description="审视人/主持人")
    health_score: Optional[int] = Field(default=None, ge=0, le=100, description="总体健康度评分")
    financial_score: Optional[int] = Field(default=None, ge=0, le=100)
    customer_score: Optional[int] = Field(default=None, ge=0, le=100)
    internal_score: Optional[int] = Field(default=None, ge=0, le=100)
    learning_score: Optional[int] = Field(default=None, ge=0, le=100)
    findings: Optional[List[str]] = Field(default=None, description="发现的问题")
    achievements: Optional[List[str]] = Field(default=None, description="取得的成果")
    recommendations: Optional[List[str]] = Field(default=None, description="改进建议")
    decisions: Optional[List[Dict[str, Any]]] = Field(default=None, description="决策事项")
    action_items: Optional[List[Dict[str, Any]]] = Field(default=None, description="行动计划")
    meeting_minutes: Optional[str] = Field(default=None, description="会议纪要")
    attendees: Optional[List[int]] = Field(default=None, description="参会人员ID列表")
    meeting_duration: Optional[int] = Field(default=None, description="会议时长（分钟）")
    next_review_date: Optional[date] = Field(default=None, description="下次审视日期")


class StrategyReviewUpdate(BaseModel):
    """更新战略审视"""
    review_date: Optional[date] = None
    review_period: Optional[str] = None
    reviewer_id: Optional[int] = None
    health_score: Optional[int] = Field(default=None, ge=0, le=100)
    financial_score: Optional[int] = Field(default=None, ge=0, le=100)
    customer_score: Optional[int] = Field(default=None, ge=0, le=100)
    internal_score: Optional[int] = Field(default=None, ge=0, le=100)
    learning_score: Optional[int] = Field(default=None, ge=0, le=100)
    findings: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    decisions: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    meeting_minutes: Optional[str] = None
    attendees: Optional[List[int]] = None
    meeting_duration: Optional[int] = None
    next_review_date: Optional[date] = None


class StrategyReviewResponse(TimestampSchema):
    """战略审视响应"""
    id: int
    strategy_id: int
    review_type: str
    review_date: date
    review_period: Optional[str] = None
    reviewer_id: Optional[int] = None
    health_score: Optional[int] = None
    financial_score: Optional[int] = None
    customer_score: Optional[int] = None
    internal_score: Optional[int] = None
    learning_score: Optional[int] = None
    findings: Optional[List[str]] = None
    achievements: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    decisions: Optional[List[Dict[str, Any]]] = None
    action_items: Optional[List[Dict[str, Any]]] = None
    meeting_minutes: Optional[str] = None
    attendees: Optional[List[int]] = None
    meeting_duration: Optional[int] = None
    next_review_date: Optional[date] = None
    is_active: bool = True

    # 扩展字段
    reviewer_name: Optional[str] = None
    attendee_names: List[str] = []
    strategy_name: Optional[str] = None


class HealthScoreResponse(BaseModel):
    """健康度评分响应"""
    strategy_id: int
    strategy_name: Optional[str] = None
    overall_score: Optional[int] = None
    overall_level: Optional[str] = None  # 健康等级
    financial_score: Optional[int] = None
    customer_score: Optional[int] = None
    internal_score: Optional[int] = None
    learning_score: Optional[int] = None
    calculation_date: Optional[date] = None
    calculated_at: Optional[datetime] = None
    dimensions: List["DimensionHealthDetail"] = []
    dimension_details: List["DimensionHealthDetail"] = []  # 兼容旧字段名
    trend: Optional[Any] = None  # 可以是 list 或 dict

    class Config:
        from_attributes = True


class DimensionHealthDetail(BaseModel):
    """维度健康度详情"""
    dimension: str
    dimension_name: str
    score: int
    health_level: str  # EXCELLENT/GOOD/WARNING/DANGER
    csf_count: int
    kpi_count: int
    kpi_completion_rate: float
    kpi_on_track: int = 0
    kpi_at_risk: int = 0
    kpi_off_track: int = 0
    issues: List[str] = []


# ============================================
# StrategyCalendarEvent - 战略日历事件
# ============================================

class StrategyCalendarEventCreate(BaseModel):
    """创建战略日历事件"""
    strategy_id: int = Field(description="关联战略")
    event_type: str = Field(description="事件类型")
    name: str = Field(max_length=200, description="事件名称")
    description: Optional[str] = Field(default=None, description="事件描述")
    year: int = Field(description="年度")
    month: Optional[int] = Field(default=None, ge=1, le=12, description="月份")
    quarter: Optional[int] = Field(default=None, ge=1, le=4, description="季度")
    scheduled_date: Optional[date] = Field(default=None, description="计划日期")
    deadline: Optional[date] = Field(default=None, description="截止日期")
    is_recurring: bool = Field(default=False, description="是否周期性")
    recurrence_rule: Optional[str] = Field(default=None, description="重复规则")
    owner_user_id: Optional[int] = Field(default=None, description="责任人")
    participants: Optional[List[int]] = Field(default=None, description="参与人员")
    reminder_days: int = Field(default=7, description="提前提醒天数")


class StrategyCalendarEventUpdate(BaseModel):
    """更新战略日历事件"""
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = None
    month: Optional[int] = Field(default=None, ge=1, le=12)
    quarter: Optional[int] = Field(default=None, ge=1, le=4)
    scheduled_date: Optional[date] = None
    actual_date: Optional[date] = None
    deadline: Optional[date] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None
    owner_user_id: Optional[int] = None
    participants: Optional[List[int]] = None
    status: Optional[str] = None
    review_id: Optional[int] = None
    reminder_days: Optional[int] = None


class StrategyCalendarEventResponse(TimestampSchema):
    """战略日历事件响应"""
    id: int
    strategy_id: int
    event_type: str
    name: str
    description: Optional[str] = None
    year: int
    month: Optional[int] = None
    quarter: Optional[int] = None
    scheduled_date: Optional[date] = None
    actual_date: Optional[date] = None
    deadline: Optional[date] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None
    owner_user_id: Optional[int] = None
    participants: Optional[List[int]] = None
    status: str = "PLANNED"
    review_id: Optional[int] = None
    reminder_days: int = 7
    reminder_sent: bool = False
    is_active: bool = True

    # 扩展字段
    owner_name: Optional[str] = None
    participant_names: List[str] = []
    strategy_name: Optional[str] = None
    event_type_name: Optional[str] = None


class CalendarMonthResponse(BaseModel):
    """月度日历响应"""
    year: int
    month: int
    events: List[StrategyCalendarEventResponse] = []

    class Config:
        from_attributes = True


class CalendarYearResponse(BaseModel):
    """年度日历响应"""
    year: int
    months: List[CalendarMonthResponse] = []
    event_summary: Dict[str, int] = {}  # 按类型统计

    class Config:
        from_attributes = True


# ============================================
# 例行管理周期
# ============================================

class RoutineManagementCycleItem(BaseModel):
    """例行管理周期项"""
    event_type: str
    event_type_name: str
    frequency: str  # MONTHLY/QUARTERLY/YEARLY
    typical_timing: str  # e.g., "每月第一周"
    participants: List[str] = []
    key_activities: List[str] = []


class RoutineManagementCycleResponse(BaseModel):
    """例行管理周期响应"""
    strategy_id: int
    year: int
    annual_events: List[RoutineManagementCycleItem] = []
    quarterly_events: List[RoutineManagementCycleItem] = []
    monthly_events: List[RoutineManagementCycleItem] = []

    class Config:
        from_attributes = True


# 更新前向引用
HealthScoreResponse.model_rebuild()
