# -*- coding: utf-8 -*-
"""
客户关系成熟度评分记录模型
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

from app.models.base import Base, TimestampMixin


class CustomerRelationshipScore(Base, TimestampMixin):
    """客户关系成熟度评分记录"""

    __tablename__ = "customer_relationship_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, comment="客户ID")
    opportunity_id = Column(Integer, ForeignKey("opportunities.id", ondelete="SET NULL"), comment="关联商机")

    # 评分日期
    score_date = Column(Date, nullable=False, comment="评分日期")

    # 六维度得分 (总分100)
    decision_chain_score = Column(Integer, default=0, comment="决策链覆盖度 (0-20)")
    interaction_frequency_score = Column(Integer, default=0, comment="互动频率 (0-15)")
    relationship_depth_score = Column(Integer, default=0, comment="关系深度 (0-20)")
    information_access_score = Column(Integer, default=0, comment="信息获取度 (0-15)")
    support_level_score = Column(Integer, default=0, comment="支持度 (0-20)")
    executive_engagement_score = Column(Integer, default=0, comment="高层互动 (0-10)")

    # 汇总
    total_score = Column(Integer, default=0, comment="总分 (0-100)")
    maturity_level = Column(String(5), comment="成熟度等级: L1-L5")
    estimated_win_rate = Column(Integer, comment="预估赢单率 %")

    # 评分详情JSON
    score_details = Column(Text, comment="各维度评分详情JSON")

    # 评分人
    scored_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    is_auto_calculated = Column(Boolean, default=True, comment="是否自动计算")

    # 关系
    customer = relationship("Customer", back_populates="relationship_scores")
    opportunity = relationship("Opportunity")
    scorer = relationship("User")

    # 索引
    __table_args__ = (
        Index("idx_rel_score_customer", "customer_id"),
        Index("idx_rel_score_date", "score_date"),
        Index("idx_rel_score_level", "maturity_level"),
        Index("idx_rel_score_opportunity", "opportunity_id"),
    )

    def __repr__(self):
        return f"<CustomerRelationshipScore {self.customer_id} - {self.maturity_level} - {self.score_date}>"
