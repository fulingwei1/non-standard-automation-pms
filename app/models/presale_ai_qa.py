"""
售前AI智能问答记录模型
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL, TIMESTAMP, JSON
from sqlalchemy.sql import func
from app.models.base import Base


class PresaleAIQA(Base):
    """AI智能问答记录表"""
    __tablename__ = 'presale_ai_qa'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='问答ID')
    question = Column(Text, nullable=False, comment='问题')
    answer = Column(Text, nullable=True, comment='答案')
    matched_cases = Column(JSON, nullable=True, comment='关联的案例IDs')
    confidence_score = Column(DECIMAL(3, 2), nullable=True, comment='置信度评分 0-1')
    feedback_score = Column(Integer, nullable=True, comment='用户反馈1-5星')
    created_by = Column(Integer, nullable=True, comment='创建人ID')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')

    def __repr__(self):
        return f"<PresaleAIQA {self.id}: {self.question[:50]}...>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'matched_cases': self.matched_cases,
            'confidence_score': float(self.confidence_score) if self.confidence_score else None,
            'feedback_score': self.feedback_score,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
