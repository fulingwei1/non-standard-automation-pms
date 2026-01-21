# -*- coding: utf-8 -*-
"""
战略年度对比模型 - StrategyComparison
"""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class StrategyComparison(Base, TimestampMixin):
    """战略年度对比"""

    __tablename__ = "strategy_comparisons"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 对比年份
    current_strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False, comment="当前战略ID")
    previous_strategy_id = Column(Integer, ForeignKey("strategies.id"), comment="对比战略ID（去年）")
    current_year = Column(Integer, nullable=False, comment="当前年份")
    previous_year = Column(Integer, comment="对比年份")

    # 生成时间
    generated_date = Column(Date, nullable=False, comment="生成日期")
    generated_by = Column(Integer, ForeignKey("users.id"), comment="生成人")

    # 总体健康度对比
    current_health_score = Column(Integer, comment="当前健康度评分")
    previous_health_score = Column(Integer, comment="去年健康度评分")
    health_change = Column(Integer, comment="健康度变化")

    # 财务维度对比
    current_financial_score = Column(Integer, comment="当前财务维度评分")
    previous_financial_score = Column(Integer, comment="去年财务维度评分")
    financial_change = Column(Integer, comment="财务维度变化")

    # 客户维度对比
    current_customer_score = Column(Integer, comment="当前客户维度评分")
    previous_customer_score = Column(Integer, comment="去年客户维度评分")
    customer_change = Column(Integer, comment="客户维度变化")

    # 内部运营维度对比
    current_internal_score = Column(Integer, comment="当前内部运营维度评分")
    previous_internal_score = Column(Integer, comment="去年内部运营维度评分")
    internal_change = Column(Integer, comment="内部运营维度变化")

    # 学习成长维度对比
    current_learning_score = Column(Integer, comment="当前学习成长维度评分")
    previous_learning_score = Column(Integer, comment="去年学习成长维度评分")
    learning_change = Column(Integer, comment="学习成长维度变化")

    # KPI 完成率对比
    kpi_completion_rate = Column(Numeric(5, 2), comment="当前KPI完成率")
    previous_kpi_completion_rate = Column(Numeric(5, 2), comment="去年KPI完成率")
    kpi_completion_change = Column(Numeric(5, 2), comment="KPI完成率变化")

    # 重点工作完成率对比
    work_completion_rate = Column(Numeric(5, 2), comment="当前重点工作完成率")
    previous_work_completion_rate = Column(Numeric(5, 2), comment="去年重点工作完成率")
    work_completion_change = Column(Numeric(5, 2), comment="重点工作完成率变化")

    # 详细分析数据
    csf_comparison = Column(Text, comment="CSF 对比详情（JSON）")
    kpi_comparison = Column(Text, comment="KPI 对比详情（JSON）")
    work_comparison = Column(Text, comment="重点工作对比详情（JSON）")

    # 分析结论
    summary = Column(Text, comment="总结")
    highlights = Column(Text, comment="亮点（JSON数组）")
    improvements = Column(Text, comment="改进点（JSON数组）")
    recommendations = Column(Text, comment="建议（JSON数组）")

    # 软删除
    is_active = Column(Boolean, default=True, comment="是否激活")

    # 关系
    current_strategy = relationship("Strategy", foreign_keys=[current_strategy_id])
    previous_strategy = relationship("Strategy", foreign_keys=[previous_strategy_id])
    generator = relationship("User", foreign_keys=[generated_by])

    __table_args__ = (
        Index("idx_strategy_comparison_current", "current_strategy_id"),
        Index("idx_strategy_comparison_previous", "previous_strategy_id"),
        Index("idx_strategy_comparison_years", "current_year", "previous_year"),
        Index("idx_strategy_comparison_date", "generated_date"),
        Index("idx_strategy_comparison_active", "is_active"),
    )

    def __repr__(self):
        return f"<StrategyComparison {self.current_year} vs {self.previous_year}>"
