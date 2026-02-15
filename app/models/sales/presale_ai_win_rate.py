# -*- coding: utf-8 -*-
"""
售前AI赢率预测模型
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from enum import Enum

from app.models.base import Base, TimestampMixin


class WinRateResultEnum(str, Enum):
    """实际结果枚举"""
    WON = "won"
    LOST = "lost"
    PENDING = "pending"


class PresaleAIWinRate(Base, TimestampMixin):
    """AI赢率预测记录表"""
    
    __tablename__ = "presale_ai_win_rate"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, nullable=False, index=True, comment="售前工单ID")
    
    # 预测结果
    win_rate_score = Column(Numeric(5, 2), comment="赢率分数 (0-100)")
    confidence_interval = Column(String(20), comment="置信区间，如：60-80%")
    
    # 详细分析（JSON格式）
    influencing_factors = Column(JSON, comment="影响因素列表: [{factor, impact, type: positive/negative}]")
    competitor_analysis = Column(JSON, comment="竞品分析: {competitors: [], our_advantages: [], competitor_advantages: [], strategy: []}")
    improvement_suggestions = Column(JSON, comment="改进建议: {short_term: [], mid_term: [], milestones: []}")
    
    # AI分析报告
    ai_analysis_report = Column(Text, comment="AI生成的完整分析报告")
    model_version = Column(String(50), comment="使用的模型版本")
    
    # 元数据
    predicted_at = Column(DateTime, default=datetime.now, comment="预测时间")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index('idx_presale_ai_win_rate_ticket', 'presale_ticket_id'),
        Index('idx_presale_ai_win_rate_score', 'win_rate_score'),
        Index('idx_presale_ai_win_rate_predicted_at', 'predicted_at'),
    )
    
    def __repr__(self):
        return f"<PresaleAIWinRate id={self.id} ticket_id={self.presale_ticket_id} score={self.win_rate_score}>"


class PresaleWinRateHistory(Base, TimestampMixin):
    """赢率历史记录表（用于模型训练和准确度评估）"""
    
    __tablename__ = "presale_win_rate_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, nullable=False, index=True, comment="售前工单ID")
    
    # 预测信息
    predicted_win_rate = Column(Numeric(5, 2), comment="预测赢率 (0-100)")
    prediction_id = Column(Integer, ForeignKey("presale_ai_win_rate.id"), comment="关联的预测记录ID")
    
    # 实际结果
    actual_result = Column(SQLEnum(WinRateResultEnum), default=WinRateResultEnum.PENDING, comment="实际结果: won/lost/pending")
    actual_win_date = Column(DateTime, comment="实际赢单日期")
    actual_lost_date = Column(DateTime, comment="实际失单日期")
    
    # 特征存储（用于模型训练）
    features = Column(JSON, comment="所有输入特征的快照")
    
    # 准确度分析
    prediction_error = Column(Numeric(5, 2), comment="预测误差 (仅当结果确定时)")
    is_correct_prediction = Column(Integer, comment="预测是否正确 (1=正确, 0=错误, NULL=待定)")
    
    # 元数据
    result_updated_at = Column(DateTime, comment="结果更新时间")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="结果更新人ID")
    
    # 关系
    prediction = relationship("PresaleAIWinRate", foreign_keys=[prediction_id])
    updater = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index('idx_presale_win_rate_history_ticket', 'presale_ticket_id'),
        Index('idx_presale_win_rate_history_result', 'actual_result'),
        Index('idx_presale_win_rate_history_prediction', 'prediction_id'),
        Index('idx_presale_win_rate_history_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<PresaleWinRateHistory id={self.id} ticket_id={self.presale_ticket_id} result={self.actual_result}>"


__all__ = [
    "PresaleAIWinRate",
    "PresaleWinRateHistory",
    "WinRateResultEnum",
]
