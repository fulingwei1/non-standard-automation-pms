# -*- coding: utf-8 -*-
"""
ECN模型 - 评估和审批
"""
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship, synonym

from ..base import Base, TimestampMixin


class EcnEvaluation(Base, TimestampMixin):
    """ECN评估表"""

    __tablename__ = "ecn_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    ecn_id = Column(Integer, ForeignKey("ecn.id"), nullable=False, comment="ECN ID")
    eval_dept = Column(String(50), nullable=False, comment="评估部门")

    # 评估人
    evaluator_id = Column(Integer, ForeignKey("users.id"), comment="评估人")
    evaluator_name = Column(String(50), comment="评估人姓名")

    # 评估内容
    impact_analysis = Column(Text, comment="影响分析")
    cost_estimate = Column(Numeric(14, 2), default=0, comment="成本估算")
    schedule_estimate = Column(Integer, default=0, comment="工期估算(天)")
    resource_requirement = Column(Text, comment="资源需求")
    resource_requirent = synonym("resource_requirement")
    risk_assessment = Column(Text, comment="风险评估")

    # 评估结论
    eval_result = Column(String(20), comment="评估结论")
    eval_opinion = Column(Text, comment="评估意见")
    conditions = Column(Text, comment="附加条件")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    evaluated_at = Column(DateTime, comment="评估时间")

    # 附件
    attachments = Column(JSON, comment="附件")

    # 关系
    ecn = relationship("Ecn", back_populates="evaluations")
    evaluator = relationship("User")

    __table_args__ = (
        Index("idx_eval_ecn", "ecn_id"),
        Index("idx_eval_dept", "eval_dept"),
        Index("idx_eval_status", "status"),
    )


class EcnApproval(Base):
    """Retired ECN approval row compatibility shell.

    Runtime ECN approvals now live in the unified approval engine
    (`approval_instances` / `approval_tasks` / `approval_action_logs`).
    This shell keeps old helper signatures importable without registering the
    retired `ecn_approvals` table in SQLAlchemy metadata.
    """

    __abstract__ = True

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
