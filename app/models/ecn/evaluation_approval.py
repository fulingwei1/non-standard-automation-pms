# -*- coding: utf-8 -*-
"""
ECN模型 - 评估和审批
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class EcnEvaluation(Base, TimestampMixin):
    """ECN评估表"""
    __tablename__ = 'ecn_evaluations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    eval_dept = Column(String(50), nullable=False, comment='评估部门')

    # 评估人
    evaluator_id = Column(Integer, ForeignKey('users.id'), comment='评估人')
    evaluator_name = Column(String(50), comment='评估人姓名')

    # 评估内容
    impact_analysis = Column(Text, comment='影响分析')
    cost_estimate = Column(Numeric(14, 2), default=0, comment='成本估算')
    schedule_estimate = Column(Integer, default=0, comment='工期估算(天)')
    resource_requirement = Column(Text, comment='资源需求')
    risk_assessment = Column(Text, comment='风险评估')

    # 评估结论
    eval_result = Column(String(20), comment='评估结论')
    eval_opinion = Column(Text, comment='评估意见')
    conditions = Column(Text, comment='附加条件')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    evaluated_at = Column(DateTime, comment='评估时间')

    # 附件
    attachments = Column(JSON, comment='附件')

    # 关系
    ecn = relationship('Ecn', back_populates='evaluations')
    evaluator = relationship('User')

    __table_args__ = (
        Index('idx_eval_ecn', 'ecn_id'),
        Index('idx_eval_dept', 'eval_dept'),
        Index('idx_eval_status', 'status'),
    )


class EcnApproval(Base, TimestampMixin):
    """ECN审批表"""
    __tablename__ = 'ecn_approvals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    approval_level = Column(Integer, nullable=False, comment='审批层级')
    approval_role = Column(String(50), nullable=False, comment='审批角色')

    # 审批人
    approver_id = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approver_name = Column(String(50), comment='审批人姓名')

    # 审批结果
    approval_result = Column(String(20), comment='审批结果')
    approval_opinion = Column(Text, comment='审批意见')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    approved_at = Column(DateTime, comment='审批时间')

    # 超时
    due_date = Column(DateTime, comment='审批期限')
    is_overdue = Column(Boolean, default=False, comment='是否超期')

    # 关系
    ecn = relationship('Ecn', back_populates='approvals')
    approver = relationship('User')

    __table_args__ = (
        Index('idx_approval_ecn', 'ecn_id'),
        Index('idx_ecn_approval_approver', 'approver_id'),
        Index('idx_approval_status', 'status'),
    )
