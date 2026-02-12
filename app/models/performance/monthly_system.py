# -*- coding: utf-8 -*-
"""
绩效模型 - 新绩效系统（月度工作总结）
"""

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class MonthlyWorkSummary(Base, TimestampMixin):
    """月度工作总结"""
    __tablename__ = 'monthly_work_summary'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='员工ID')
    period = Column(String(7), nullable=False, comment='评价周期 (格式: YYYY-MM)')

    # 工作总结内容（必填）
    work_content = Column(Text, nullable=False, comment='本月工作内容')
    self_evaluation = Column(Text, nullable=False, comment='自我评价')

    # 工作总结内容（选填）
    highlights = Column(Text, comment='工作亮点')
    problems = Column(Text, comment='遇到的问题')
    next_month_plan = Column(Text, comment='下月计划')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 提交时间
    submit_date = Column(DateTime, comment='提交时间')

    # 关系
    employee = relationship('User', foreign_keys=[employee_id])
    evaluations = relationship('PerformanceEvaluationRecord', back_populates='summary')

    __table_args__ = (
        Index('idx_monthly_summary_employee', 'employee_id'),
        Index('idx_monthly_summary_period', 'period'),
        Index('idx_monthly_summary_status', 'status'),
        Index('uk_employee_period', 'employee_id', 'period', unique=True),
        {'comment': '月度工作总结表'}
    )


class PerformanceEvaluationRecord(Base, TimestampMixin):
    """绩效评价记录"""
    __tablename__ = 'performance_evaluation_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    summary_id = Column(Integer, ForeignKey('monthly_work_summary.id'), nullable=False, comment='工作总结ID')
    evaluator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评价人ID')
    evaluator_type = Column(String(20), nullable=False, comment='评价人类型')

    # 项目信息（仅项目经理评价时使用）
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    project_weight = Column(Integer, comment='项目权重 (多项目时使用)')

    # 评价内容
    score = Column(Integer, nullable=False, comment='评分 (60-100)')
    comment = Column(Text, nullable=False, comment='评价意见')

    # 任职资格相关字段
    qualification_level_id = Column(Integer, ForeignKey('qualification_level.id'), comment='任职资格等级ID')
    qualification_score = Column(JSON, comment='任职资格维度得分 (JSON格式)')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    evaluated_at = Column(DateTime, comment='评价时间')

    # 关系
    summary = relationship('MonthlyWorkSummary', back_populates='evaluations')
    evaluator = relationship('User', foreign_keys=[evaluator_id])
    project = relationship('Project', foreign_keys=[project_id])
    qualification_level = relationship('QualificationLevel', foreign_keys=[qualification_level_id])

    __table_args__ = (
        Index('idx_eval_record_summary', 'summary_id'),
        Index('idx_eval_record_evaluator', 'evaluator_id'),
        Index('idx_eval_record_project', 'project_id'),
        Index('idx_eval_record_status', 'status'),
        Index('idx_eval_record_qual_level', 'qualification_level_id'),
        {'comment': '绩效评价记录表'}
    )


class EvaluationWeightConfig(Base, TimestampMixin):
    """评价权重配置"""
    __tablename__ = 'evaluation_weight_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    dept_manager_weight = Column(Integer, nullable=False, default=50, comment='部门经理权重 (%)')
    project_manager_weight = Column(Integer, nullable=False, default=50, comment='项目经理权重 (%)')
    effective_date = Column(Date, nullable=False, comment='生效日期')
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='操作人ID')
    reason = Column(Text, comment='调整原因')

    # 关系
    operator = relationship('User', foreign_keys=[operator_id])

    __table_args__ = (
        Index('idx_weight_config_effective_date', 'effective_date'),
        {'comment': '评价权重配置表'}
    )
