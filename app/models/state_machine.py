# -*- coding: utf-8 -*-
"""
状态机相关模型

统一状态转换审计日志
"""

from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class StateTransitionLog(Base, TimestampMixin):
    """
    统一状态转换审计日志表

    记录所有使用状态机的实体的状态转换历史，提供：
    - 完整的审计追踪
    - 统一的查询接口
    - 操作人追踪
    - 业务备注记录
    """
    __tablename__ = "state_transition_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    entity_type = Column(String(50), nullable=False, comment="实体类型：ISSUE/ECN/PROJECT等")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    from_state = Column(String(50), nullable=False, comment="源状态")
    to_state = Column(String(50), nullable=False, comment="目标状态")
    operator_id = Column(Integer, ForeignKey("users.id"), comment="操作人ID")
    operator_name = Column(String(100), comment="操作人姓名（冗余字段）")
    action_type = Column(String(50), comment="操作类型：SUBMIT/APPROVE/REJECT/ASSIGN等")
    comment = Column(Text, comment="备注/原因")
    extra_data = Column(JSON, comment="额外数据（如通知接收人、附件等）")

    # 关系
    operator = relationship("User", foreign_keys=[operator_id])

    __table_args__ = (
        Index("idx_state_log_entity", "entity_type", "entity_id"),
        Index("idx_state_log_operator", "operator_id"),
        Index("idx_state_log_created", "created_at"),
        {"comment": "统一状态转换审计日志表"}
    )

    def __repr__(self):
        return f"<StateTransitionLog {self.entity_type}:{self.entity_id} {self.from_state}→{self.to_state}>"
