"""
AI客户情绪分析记录模型
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, TIMESTAMP, ForeignKey, JSON
from sqlalchemy.sql import func
from app.models.base import Base
import enum


class SentimentType(str, enum.Enum):
    """情绪类型"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class ChurnRiskLevel(str, enum.Enum):
    """流失风险等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class PresaleAIEmotionAnalysis(Base):
    """AI客户情绪分析记录表"""
    __tablename__ = "presale_ai_emotion_analysis"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, ForeignKey("presale_tickets.id"), nullable=False, index=True, comment="售前工单ID")
    customer_id = Column(Integer, nullable=False, index=True, comment="客户ID")
    communication_content = Column(Text, comment="沟通内容")
    sentiment = Column(Enum(SentimentType), comment="情绪类型")
    purchase_intent_score = Column(DECIMAL(5, 2), comment="购买意向评分(0-100)")
    churn_risk = Column(Enum(ChurnRiskLevel), comment="流失风险等级")
    emotion_factors = Column(JSON, comment="影响情绪的因素")
    analysis_result = Column(Text, comment="分析结果详情")
    created_at = Column(TIMESTAMP, server_default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<PresaleAIEmotionAnalysis(id={self.id}, ticket_id={self.presale_ticket_id}, sentiment={self.sentiment})>"
