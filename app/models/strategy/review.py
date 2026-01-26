# -*- coding: utf-8 -*-
"""
战略审视模型 - StrategyReview, StrategyCalendarEvent
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class StrategyReview(Base, TimestampMixin):
    """战略审视记录"""

    __tablename__ = "strategy_reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="关联战略")

    # 审视信息
    review_type = Column(String(20), nullable=False, comment="审视类型：ANNUAL/QUARTERLY/MONTHLY/SPECIAL")
    review_date = Column(Date, nullable=False, comment="审视日期")
    review_period = Column(String(20), comment="审视周期，如 2026-Q1")

    # 审视人
    reviewer_id = Column(Integer, ForeignKey("users.id"), comment="审视人/主持人")

    # 健康度评分
    health_score = Column(Integer, comment="总体健康度评分（0-100）")
    financial_score = Column(Integer, comment="财务维度评分")
    customer_score = Column(Integer, comment="客户维度评分")
    internal_score = Column(Integer, comment="内部运营维度评分")
    learning_score = Column(Integer, comment="学习成长维度评分")

    # 发现与建议
    findings = Column(Text, comment="发现的问题（JSON数组）")
    achievements = Column(Text, comment="取得的成果（JSON数组）")
    recommendations = Column(Text, comment="改进建议（JSON数组）")
    decisions = Column(Text, comment="决策事项（JSON数组）")
    action_items = Column(Text, comment="行动计划（JSON数组）")

    # 会议信息
    meeting_minutes = Column(Text, comment="会议纪要")
    attendees = Column(Text, comment="参会人员（JSON数组）")
    meeting_duration = Column(Integer, comment="会议时长（分钟）")

    # 下次审视
    next_review_date = Column(Date, comment="下次审视日期")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    strategy = relationship("Strategy", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    __table_args__ = (
        Index("idx_strategy_reviews_strategy", "strategy_id"),
        Index("idx_strategy_reviews_type", "review_type"),
        Index("idx_strategy_reviews_date", "review_date"),
        Index("idx_strategy_reviews_active", "is_active"),
    )

    def __repr__(self):
        return f"<StrategyReview strategy={self.strategy_id} date={self.review_date}>"


class StrategyCalendarEvent(Base, TimestampMixin):
    """战略日历事件 - 例行管理节点"""

    __tablename__ = "strategy_calendar_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="关联战略")

    # 事件基本信息
    event_type = Column(String(30), nullable=False, comment="事件类型：ANNUAL_PLANNING/QUARTERLY_REVIEW/MONTHLY_TRACKING/KPI_COLLECTION/DECOMPOSITION/ASSESSMENT")
    name = Column(String(200), nullable=False, comment="事件名称")
    description = Column(Text, comment="事件描述")

    # 时间
    year = Column(Integer, nullable=False, comment="年度")
    month = Column(Integer, comment="月份")
    quarter = Column(Integer, comment="季度")
    scheduled_date = Column(Date, comment="计划日期")
    actual_date = Column(Date, comment="实际日期")
    deadline = Column(Date, comment="截止日期")

    # 周期设置
    is_recurring = Column(Boolean, default=False, comment="是否周期性")
    recurrence_rule = Column(String(50), comment="重复规则：MONTHLY/QUARTERLY/YEARLY")

    # 责任人
    owner_user_id = Column(Integer, ForeignKey("users.id"), comment="责任人")
    participants = Column(Text, comment="参与人员（JSON数组）")

    # 状态
    status = Column(String(20), default="PLANNED", comment="状态：PLANNED/IN_PROGRESS/COMPLETED/CANCELLED")

    # 关联审视记录
    review_id = Column(Integer, ForeignKey("strategy_reviews.id"), comment="关联审视记录")

    # 提醒设置
    reminder_days = Column(Integer, default=7, comment="提前提醒天数")
    reminder_sent = Column(Boolean, default=False, comment="是否已发送提醒")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    strategy = relationship("Strategy", back_populates="calendar_events")
    owner = relationship("User", foreign_keys=[owner_user_id])
    review = relationship("StrategyReview")

    __table_args__ = (
        Index("idx_calendar_events_strategy", "strategy_id"),
        Index("idx_calendar_events_type", "event_type"),
        Index("idx_calendar_events_year", "year"),
        Index("idx_calendar_events_month", "month"),
        Index("idx_calendar_events_date", "scheduled_date"),
        Index("idx_calendar_events_status", "status"),
        Index("idx_calendar_events_active", "is_active"),
    )

    def __repr__(self):
        return f"<StrategyCalendarEvent {self.event_type} {self.scheduled_date}>"
