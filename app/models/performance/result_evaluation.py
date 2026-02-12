# -*- coding: utf-8 -*-
"""
绩效模型 - 结果和评价
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class PerformanceResult(Base, TimestampMixin):
    """绩效结果"""
    __tablename__ = 'performance_result'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), nullable=False, comment='考核周期ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    department_id = Column(Integer, comment='部门ID')
    department_name = Column(String(100), comment='部门名称')

    # 综合得分
    total_score = Column(Numeric(5, 2), comment='综合得分')
    level = Column(String(20), comment='绩效等级')

    # 分项得分
    workload_score = Column(Numeric(5, 2), comment='工作量得分')
    task_score = Column(Numeric(5, 2), comment='任务得分')
    quality_score = Column(Numeric(5, 2), comment='质量得分')
    collaboration_score = Column(Numeric(5, 2), comment='协作得分')
    growth_score = Column(Numeric(5, 2), comment='成长得分')

    # 详细数据
    indicator_scores = Column(JSON, comment='各指标详细得分(JSON)')

    # 排名
    dept_rank = Column(Integer, comment='部门排名')
    company_rank = Column(Integer, comment='公司排名')

    # 环比
    score_change = Column(Numeric(5, 2), comment='得分变化')
    rank_change = Column(Integer, comment='排名变化')

    # 亮点与待改进
    highlights = Column(JSON, comment='亮点(JSON)')
    improvements = Column(JSON, comment='待改进(JSON)')

    # 状态
    status = Column(String(20), default='CALCULATED', comment='状态')

    # 计算时间
    calculated_at = Column(DateTime, comment='计算时间')

    # 部门经理调整字段（新增）
    original_total_score = Column(Numeric(5, 2), comment='原始综合得分（调整前）')
    adjusted_total_score = Column(Numeric(5, 2), comment='调整后综合得分')
    original_dept_rank = Column(Integer, comment='原始部门排名（调整前）')
    adjusted_dept_rank = Column(Integer, comment='调整后部门排名')
    original_company_rank = Column(Integer, comment='原始公司排名（调整前）')
    adjusted_company_rank = Column(Integer, comment='调整后公司排名')
    adjustment_reason = Column(Text, comment='调整理由（必填）')
    adjusted_by = Column(Integer, ForeignKey('users.id'), comment='调整人ID（部门经理）')
    adjusted_at = Column(DateTime, comment='调整时间')
    is_adjusted = Column(Boolean, default=False, comment='是否已调整')

    # 关系
    period = relationship('PerformancePeriod', back_populates='results')
    evaluations = relationship('PerformanceEvaluation', back_populates='result')
    adjustment_history = relationship('PerformanceAdjustmentHistory', back_populates='result', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_perf_result_period', 'period_id'),
        Index('idx_perf_result_user', 'user_id'),
        Index('idx_perf_result_dept', 'department_id'),
        Index('idx_perf_result_score', 'total_score'),
        Index('idx_perf_result_adjusted', 'is_adjusted'),
        {'comment': '绩效结果表'}
    )


class PerformanceEvaluation(Base, TimestampMixin):
    """绩效评价（上级评语）"""
    __tablename__ = 'performance_evaluation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    result_id = Column(Integer, ForeignKey('performance_result.id'), nullable=False, comment='绩效结果ID')

    # 评价人
    evaluator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评价人ID')
    evaluator_name = Column(String(50), comment='评价人姓名')
    evaluator_role = Column(String(50), comment='评价人角色')

    # 评价内容
    overall_comment = Column(Text, comment='总体评价')
    strength_comment = Column(Text, comment='优点评价')
    improvement_comment = Column(Text, comment='改进建议')

    # 调整
    adjusted_level = Column(String(20), comment='调整后等级')
    adjustment_reason = Column(Text, comment='调整原因')

    # 评价时间
    evaluated_at = Column(DateTime, default=datetime.now, comment='评价时间')

    # 关系
    result = relationship('PerformanceResult', back_populates='evaluations')

    __table_args__ = (
        Index('idx_perf_eval_result', 'result_id'),
        Index('idx_perf_eval_evaluator', 'evaluator_id'),
        {'comment': '绩效评价表'}
    )
