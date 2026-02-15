"""
情绪趋势模型
"""
from sqlalchemy import Column, Integer, JSON, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class PresaleEmotionTrend(Base):
    """情绪趋势表"""
    __tablename__ = "presale_emotion_trend"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, ForeignKey("presale_tickets.id"), nullable=False, index=True, comment="售前工单ID")
    customer_id = Column(Integer, nullable=False, index=True, comment="客户ID")
    trend_data = Column(JSON, comment="趋势数据 [{date, sentiment, intent_score}]")
    key_turning_points = Column(JSON, comment="关键转折点")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<PresaleEmotionTrend(id={self.id}, ticket_id={self.presale_ticket_id}, customer_id={self.customer_id})>"
