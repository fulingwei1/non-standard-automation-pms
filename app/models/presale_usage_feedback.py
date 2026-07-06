# -*- coding: utf-8 -*-
"""
售前智能体使用反馈模型。

记录销售使用智能体的反馈，用于AI学习和改进：
  - 是否使用了AI产出（方案/资料包/建议）
  - 使用效果（成单/未成单/部分采用）
  - 客户反馈（接受/拒绝/修改）
  - 销售评价（有用/一般/没用）
  - 改进建议（销售觉得AI哪里可以改进）

这个数据闭环让AI越用越聪明。
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.models.base import Base


class PresaleUsageFeedback(Base):
    """售前智能体使用反馈"""

    __tablename__ = "presale_usage_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联的智能体产出
    proposal_id = Column(Integer, nullable=True, comment="关联的方案ID（presale_proposals.id）")
    audit_pack_id = Column(Integer, nullable=True, comment="关联的验厂资料ID（audit_pack_requests.id）")
    coach_session_id = Column(Integer, nullable=True, comment="关联的销售教练会话ID")
    
    # 使用信息
    used = Column(Integer, default=1, comment="是否使用了AI产出（1=用了 0=没用）")
    usage_scenario = Column(String(50), comment="使用场景（方案生成/验厂资料/销售教练/竞争分析）")
    
    # 效果反馈
    outcome = Column(String(50), comment="结果（成单/未成单/部分采用/进行中）")
    customer_feedback = Column(String(50), comment="客户反馈（接受/拒绝/修改/无反馈）")
    
    # 销售评价
    rating = Column(Integer, comment="销售评分（1-5分）")
    rating_comment = Column(Text, comment="评分说明")
    
    # 改进建议
    improvement_suggestion = Column(Text, comment="改进建议（销售觉得AI哪里可以改进）")
    
    # 提交人
    submitted_by = Column(Integer, comment="提交人ID（销售）")
    submitted_by_name = Column(String(100), comment="提交人姓名")
    
    # 时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "proposal_id": self.proposal_id,
            "audit_pack_id": self.audit_pack_id,
            "usage_scenario": self.usage_scenario,
            "used": self.used,
            "outcome": self.outcome,
            "customer_feedback": self.customer_feedback,
            "rating": self.rating,
            "rating_comment": self.rating_comment,
            "improvement_suggestion": self.improvement_suggestion,
            "submitted_by_name": self.submitted_by_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
